from __future__ import with_statement
import os
import sys
import urllib
import glob
from shutil import copyfile
from usace.cavi.script import CAVI
import hec2
from com.rma.model import Project
from javax.swing    import JButton, JDialog, JOptionPane, JEditorPane, UIManager
#import traceback
import xml.etree.ElementTree as ET
import datetime
import tempfile, shutil
import json	
import zipfile
import webbrowser

cwms_home = os.getcwd()
watershed_path = Project.getCurrentProject().getProjectDirectory()
################################################################################
def get_remote_data(url):
	try:
		f = urllib.urlopen(url)
		content = f.read()
		f.close()
	except:
		print('Unable to get url contents')
		return False

	if f.code == 404:
		return False

	return content
################################################################################
def download_file(url, dest):
	try:
		print 'Downloading {} to {}'.format(url, dest)
		urllib.urlretrieve(url, dest)
		print("Download Complete!")
	except:
		raise Exception('Unable to download from: {}'.format(url))
################################################################################
#credit: https://stackoverflow.com/questions/12683834/how-to-copy-directory-recursively-in-python-and-overwrite-all
def recursive_overwrite(src, dest, ignore=None):
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files = os.listdir(src)
        if ignore is not None:
            ignored = ignore(src, files)
        else:
            ignored = set()
        for f in files:
            if f not in ignored:
                recursive_overwrite(os.path.join(src, f), 
                                    os.path.join(dest, f), 
                                    ignore)
    else:
        shutil.copyfile(src, dest)
#################################################################################
def script_downloader(remote_repo, selection, appConfig):
	
	update_libs = bool(appConfig['scripts'][selection]['update_libs'])
	config_files = appConfig['scripts'][selection]['config_files']
	watershed_path = Project.getCurrentProject().getProjectDirectory()
	ws_script_dir = os.path.join(watershed_path, 'scripts')

	scriptSrcURL = '{}/{}/{}'.format(remote_repo, appConfig['scripts'][selection]['remote_dir'], appConfig['scripts'][selection]['filename'])
	print(scriptSrcURL)

	scriptDstFilePath = os.path.join(ws_script_dir, appConfig['scripts'][selection]['filename'])
	print scriptDstFilePath

	# Copy the script file
	if get_remote_data(scriptSrcURL):
		try:
			download_file(scriptSrcURL, scriptDstFilePath)
		except:
			JOptionPane.showMessageDialog(None, "Download failed for script '"+selection+"'", "Copy Error", JOptionPane.ERROR_MESSAGE)
			return

	else:
		JOptionPane.showMessageDialog(None, "Source File doesn't seem to exist for '"+selection+"'\n"+scriptSrcURL, \
		"Something went wrong :-(", JOptionPane.ERROR_MESSAGE)
		return

	#################################################################
	# Check for script config files - These will only be downloaded
	# if they don't exist in the local watershed/shared dir
	#################################################################

	print(config_files)
	print('Config file count: {}'.format(len(config_files)))

	if len(config_files) > 0:	
		
		config_files_dir = os.path.join(watershed_path, 'shared')

		# Keep track of what was actually downloaded
		downloaded_configs = []
		
		for fname in config_files:
			fileSrcURL = '{}/{}/{}/{}'.format(remote_repo, appConfig['scripts'][selection]['remote_dir'], 'shared', fname)
			fileDstPath = os.path.join(config_files_dir, fname)
			if not os.path.isfile(fileDstPath):
				download_file(fileSrcURL, fileDstPath)
				downloaded_configs.append(fileDstPath)
			else:
				print 'Skipping download of config file: {}'.format(fname)

	
	try:
		temp_dir = tempfile.mkdtemp()
		print 'created temp folder {}'.format(temp_dir)
		
		# Download the master repo zip for the library packages		
		repo_url_parts = remote_repo.split('/')
		repo_url_parts[2] = 'github.com'
		repo_url_parts[5] = 'archive'
		repo_url_parts.append('master.zip')
		zip_url = '/'.join(repo_url_parts)

		download_file(zip_url, temp_dir+'/master.zip')

		with zipfile.ZipFile(os.path.join(temp_dir, 'master.zip'), "r") as z:
			z.extractall(temp_dir)

			print('--Files in temp folder--')
			for f in os.listdir(temp_dir):
				print(f)
				if os.path.isdir(os.path.join(temp_dir, f)):
										
					pkg_dir_src = os.path.join(temp_dir, f, 'appdata', 'rsgis')
					pkg_dir_dst = os.path.join(os.getenv('APPDATA'), 'rsgis')

					print('*'*50)
					print('Copying repo libraries...')
					print 'From: {}'.format(pkg_dir_src)
					print 'To: {}'.format(pkg_dir_dst)
					print('*'*50)

					# Copy the packages/libs from temp folder to destination
					recursive_overwrite(pkg_dir_src, pkg_dir_dst)				
					
					# Check for 3rd party libraries that need to be downloaded
					#------------------------------------------------------------
					for lib_name, lib_obj in appConfig['third_party_libs'].items():
						filename = os.path.basename(lib_obj['url'])
						lib_dest_dir = os.path.join(os.getenv('APPDATA'), 'rsgis', lib_name)
						version_file = os.path.join(lib_dest_dir, 'version.json')
						
						download_lib = True

						if os.path.isfile(version_file):
							print 'Loading json file {}'.format(version_file)
							with open(version_file) as json_file:
								version = json.load(json_file)['version']							
								if version == lib_obj['version']:
									download_lib = False
									print 'Will not download lib: {}'.format(lib_name)
						
						
						if download_lib:

							dest_file = os.path.join(lib_dest_dir, filename)
							download_file(lib_obj['url'], dest_file)

							if zipfile.is_zipfile(dest_file):
								with zipfile.ZipFile(dest_file, "r") as z:
									z.extractall(lib_dest_dir)

								# Delete the zip file
								os.remove(dest_file)							
							
							# Write the version to json file for comparison later
							with open(version_file, 'w') as outfile:
								json.dump(lib_obj, outfile)
					#------------------------------------------------------------

	except:
		print('Unable to create temp folder')
		print "Unexpected error:", sys.exc_info()
	finally:
		shutil.rmtree(temp_dir)
		print 'removing {}'.format(temp_dir)

	try:
		help_url = appConfig['scripts'][selection]['help_url']
	except:
		help_url = None
	
	msg = 'Script downloaded for '+selection
	if len(downloaded_configs) > 0:
		msg += '\n\nThe following configuration file(s) have been downloaded:'
		for cf in downloaded_configs:
			msg += '\n'+cf
	
	if help_url is not None:
		webbrowser.open(help_url, new=2, autoraise=True)
	
	JOptionPane.showMessageDialog(None, msg, "Success", JOptionPane.INFORMATION_MESSAGE)
################################################################################
def getAppConfig(filePath):
	try:
		# Read from the config file
		with open(filePath) as f:
			json_data = json.load(f)
			return json_data
	except:
		return False
################################################################################
def isScriptButtonAdded(filename):

	configFile = watershed_path+'/cavi/watershedScripts.xml'
	scriptPresent = False

	if os.path.isfile(configFile):
		tree = ET.parse(configFile)
		root = tree.getroot()
		for scriptType in root.findall('FORECAST'):
			#print scriptType
			for script in scriptType.findall('Script'):
				#print script.attrib
				if script.attrib['File'] == filename:
					return True

	# Return False - Default if node not found in XML file
	return False
################################################################################
def main():

	code_version = '19Oct2020'
	# Get the config file stored on Github.
	# This allows new scripts to be added without this script needing to be replaced on every PC/Server Watershed

	remote_repo = "https://raw.githubusercontent.com/usace/rts-utils/master"

	remote_config = get_remote_data(remote_repo+'/script_downloader/downloader_config.json')
	# Verify remote data was returned, otherwise exit
	if remote_config == False:
		errMsg = 'Failed to read remote config file.\n'
		JOptionPane.showMessageDialog(None, errMsg, "Config Error", JOptionPane.ERROR_MESSAGE)
		return

	appConfig = json.loads(remote_config)

	# Check to see if script downloader needs to be updated (by itself)
	fileVersion = appConfig['version']
	code_version_dt = datetime.datetime.strptime(code_version, '%d%b%Y')
	file_version_dt = datetime.datetime.strptime(fileVersion, '%d%b%Y')

	if code_version_dt < file_version_dt:
		msg = "Script Downloader is out of date, please update using this script.\nLatest version: "\
		+appConfig['version']+'\nYour version: '+code_version
		JOptionPane.showMessageDialog(None, msg, "Version Check", JOptionPane.ERROR_MESSAGE)
	else:
		print('Script Downloader Version is current.')

	choices = appConfig['scripts'].keys()

	selection = JOptionPane.showInputDialog(
			None,                                               # dialog parent component
			"Select the script to downloader",             		# message
			"Script Downloader - v"+code_version,         		# title
			JOptionPane.PLAIN_MESSAGE,                          # message type (sets default icon)
			None,                                               # icon to override default
			choices,                                            # list of selections
			choices[0])                                         # initial selection

	# If cancel was clicked
	if selection is None:
		return

	script_filename = appConfig['scripts'][selection]['filename']	

	script_downloader(remote_repo, selection, appConfig)
################################################################################
if __name__ == '__main__':
	main()