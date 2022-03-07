package main

import (
	"log"
	"os"

	"github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/plumbing"
)

func goGitClone(d string, o *git.CloneOptions) error {
	r, err := git.PlainClone(d, false, o)
	if err != nil {
		return err
	}

	ref, _ := r.Head()
	// ... retrieving the commit object
	commit, _ := r.CommitObject(ref.Hash())

	log.Println(commit)

	return nil
}

func goGitPull(r *git.Repository, po *git.PullOptions) error {
	w, err := r.Worktree()
	if err != nil {
		return err
	}

	if err = w.Pull(po); err != nil {
		return err
	}

	ref, err := r.Head()
	if err != nil {
		return err
	}

	commit, err := r.CommitObject(ref.Hash())
	if err != nil {
		return err
	}
	log.Println(commit)
	return nil
}

func goGitRepo(u string, remote string, ref plumbing.ReferenceName, d string) error {

	pullOptions := git.PullOptions{
		RemoteName:    remote,
		ReferenceName: ref,
		SingleBranch:  true,
		Progress:      os.Stdout,
	}
	cloneOptions := git.CloneOptions{
		URL:           u,
		RemoteName:    remote,
		ReferenceName: ref,
		SingleBranch:  true,
		Progress:      os.Stdout,
	}

	r, err := git.PlainOpen(d)
	if err == git.ErrRepositoryNotExists {
		if err := goGitClone(d, &cloneOptions); err != nil {
			return err
		}
		return nil
	}

	if err := goGitPull(r, &pullOptions); err != nil {
		return err
	}

	return nil
}
