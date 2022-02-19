from datetime import date, datetime
from java.time.format import DateTimeFormatterBuilder, DateTimeFormatter
from java.time import ZoneId, LocalDateTime, ZonedDateTime




class TimeFormatter():
    ''' Java time formatter/builder dealing with different date time formats '''
    def __init__(self, zid=ZoneId.of("UTC")):
        self.zid = zid
        self.fb = self.format_builder()

    def format_builder(self):
        '''
        Return DateTimeFormatter

        Used to define the datetime format allowing for proper parsing.
        '''
        fb = DateTimeFormatterBuilder()
        fb.parseCaseInsensitive()
        fb.appendPattern("[[d][dd]MMMyyyy[[,][ ][:][Hmm[ss]][H:mm[:ss]][HHmm][HH:mm[:ss]]]]" + \
            "[[d][dd]-[M][MM][MMM]-yyyy[[,] [Hmm[ss]][H:mm[:ss]][HHmm][HH:mm[:ss]]]]" + \
            "[yyyy-[M][MM][MMM]-[d][dd][['T'][ ][Hmm[ss]][H:mm[:ss]][HHmm[ss]][HH:mm[:ss]]]]")
        return fb.toFormatter()

    def iso_instant(self):
        '''
        Return DateTimeFormatter ISO_INSTANT

        Datetime format will be in the form '2020-12-03T10:15:30Z'
        '''
        return DateTimeFormatter.ISO_INSTANT
        
    def parse_local_date_time(self,t):
        '''
        Return LocalDateTime

        Input is a java.lang.String parsed to LocalDateTime
        '''
        return LocalDateTime.parse(t,self.fb)

    def parse_zoned_date_time(self,t, z):
        '''
        Return ZonedDateTime

        Input is a java.lang.String parsed to LocalDateTime and ZoneId applied.
        '''
        ldt = self.parse_local_date_time(t)
        return ZonedDateTime.of(ldt, z)

if __name__ == "__main__":
    tf = TimeFormatter()
    tz = tf.zid
    st = tf.parse_zoned_date_time("2022-02-02T12:00:00", tz)
    et = tf.parse_zoned_date_time("2022-02-12T12:00:00", tz)

    print(st, et)