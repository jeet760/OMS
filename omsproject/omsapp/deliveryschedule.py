from datetime import datetime,timedelta

class DeliverySchedule:
    def __init__(self):
        #print('Hello Kunu.')
        now = datetime.today().time().__format__('%H:%M:%S')
        current_time = datetime.strptime(now, '%H:%M:%S').time()
        cutoff_time = datetime.strptime('16:00:00', '%H:%M:%S').time()

        today = datetime.today().date()

        if current_time > cutoff_time:
            today = today+timedelta(days=1)

        #print(f'Today is {today}')
        dateSeriesRange = 8
        self.dateSeries = []
        self.timeSeries = ['06:00 - 08:00', '08:00 - 10:00', '10:00 - 12:00', '12:00 - 14:00', '14:00 - 16:00']
        for i in range(1, dateSeriesRange):
            series_date = today+timedelta(days=i)
            self.dateSeries.append(series_date.__format__('%d-%m-%Y'))

    def __iter__(self):
        return self.dateSeries, self.timeSeries