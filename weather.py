from datetime import datetime
import urllib2
import json
import string
import sys
import time

#api keys and base url
owm_apikey = ''
gtz_api_key = ""
owm_urlbase = 'http://api.openweathermap.org/data/2.5/'
gtz_urlbase = 'https://maps.googleapis.com/maps/api/timezone/'

city_dict ={}
city_country={}

#city id mapping - moving to web server using a web call to return id

# prepare_city_id_mapping
# load city.list.json from same local location to memory
def prepare_city_id_mapping():
	city_mapping_file = open('city.list.json','r')
	city_lines = city_mapping_file.readlines()
	ttl_record = len(city_lines)
	i = 1
	for line in city_lines:
		city_json = json.loads(line)
		city_dict.update({city_json['_id']:city_json['name']})
		city_country.update({city_json['_id']:city_json['name']+','+city_json['country']})
		i += 1
		if i % 2000 == 0 or i == ttl_record:
			sys.stdout.write("Loading: %d%% \r" %(float(i)/float(ttl_record)*100))
			sys.stdout.flush()	
	city_mapping_file.close()

# get_city_list
# check if user input city name in the list
# if not in the given list, then let user choose if using city name to get a close location weather
# return city id or str 'name' to indicate query by city name directly

def get_city_list(city):
	city_id_dict={}
	for _id, name in city_dict.items():
		if name == city:
			city_id_dict.update({city_country[_id]:_id})
	if len(city_id_dict)>0:
		return city_id_dict
	else:
		return 'name'

def get_owm_city_id(city):
	i = 3
	while i>0:
		url = owm_urlbase + 'find?q=' + city + '&type=like&APPID=' + owm_apikey
		req = urllib2.Request(url)
		try:
			response = urllib2.urlopen(req)
			response_data = response.read()
			city_data = json.loads(response_data)
			# import pdb
			# pdb.set_trace()
			if city_data['cod'] == '200':
				if city_data['count']>1:
					city_id_dict ={}
					for i in range(city_data['count']):
						temp_city = city_data['list'][i]
						if temp_city['id'] == 0:
							continue
						city_id_dict.update({temp_city['sys']['country']+','+ temp_city['name']:temp_city['id']})
					
					city_id = get_city_id(city_id_dict)
				else:
					city_id = city_data['list'][0]['id']
					if city_id == 0:
						continue
					print 'Weather result for:\n' + city_data['list'][0]['sys']['country'] + ',' + city_data['list'][0]['name']
					print "\nPlease try other name if current result was't correct."
			else:
				print 'City not found! Please try other name.'
				city = get_user_input('city')		
				if city == 'Q':
					exit(0)
				continue

			return city_id
		except urllib2.HTTPError as err:
			print "HTTP Error:\nError code:%d %s" %(err.code, err.msg)
			i -= 1
			if err.code >= 500:
				for sec in range(5):
					time.sleep(1)
					sys.stdout.write("Retry in %d second(s)\r" %(sec+1))
					sys.stdout.flush()
			continue

	print "Request can't be completed. Please try later."
	exit(0)		

def get_city_weather(query_city, weather_type, result_unit):
	# import pdb
	# pdb.set_trace()
	i = 3
	while i>0:
		try:
			url = owm_urlbase + weather_type + '?id=' + str(query_city) + result_unit + '&APPID=' + owm_apikey
			req = urllib2.Request(url)
			response = urllib2.urlopen(req)
			weather_data = response.read()
			weather_result = json.loads(weather_data)
			return weather_result

		except urllib2.HTTPError as err:
			i -= 1
			print "HTTP Error:\nError code:%d %s" %(err.code, err.msg)
			if err.code >= 500:
				for sec in range(5):
					time.sleep(1)
					sys.stdout.write("Retry in %d second(s)\r" %(sec+1))
					sys.stdout.flush()
			continue

	print "Request can't be completed. Please try later."
	exit(0)

def change_unit(unit_type):
	if unit_type == 'F':
		return "&units=imperial"
	else:
		return ""

def get_user_input(choice):
	if choice == 'choice':
		query_city = raw_input('Please choose the city by typing the number:')
	elif choice == 'city':
		query_city = raw_input("Please enter a city name or 'q' to quit:\nCity name:")
		query_city = string.capitalize(query_city.rstrip())

	return query_city

def get_city_id(city_list):
	if len(city_list)>1:
		i = 1
		for city, _id in city_list.items():
			print '%d: %s' %(i, city)
			i+=1
		while True:
			try:
				city_index = get_user_input('choice')
				city_index = int(city_index)
				if city_index>len(city_list) or city_index<=0:
					print 'please input a valid number. %d is not in the list.' %(city_index)
			except ValueError:
				print 'Please input the index number.'
				continue
			if city_index<=len(city_list) and city_index>0:
				break

		city_name, city_id = city_list.items()[city_index-1]
	else:
		city_name, city_id = city_list.items()[0]

	return city_id

def convert_to_local(coord, timestamp):
	# convert to local time
	coord_lon = coord['lon']
	coord_lat = coord['lat']
	concat_coord = repr(coord_lat) + ',' + repr(coord_lon)

	url = gtz_urlbase + "json?location="+concat_coord+"&timestamp="+str(timestamp)+"&key="+gtz_api_key

	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	response_data = response.read()
	time_zone = json.loads(response_data)
	tz_raw_offset = time_zone['rawOffset']
	tz_dst_offset = time_zone['dstOffset']
	total_offset = tz_dst_offset + tz_raw_offset
	return total_offset

def print_weather_current(city_weather, result_unit):
	if result_unit == "&units=metric":
		unit = u'\xb0'
		unit = unit.encode('utf8') + 'C'
	elif result_unit == "&units=imperial":
		unit = u'\xb0'
		unit = unit.encode('utf8') + 'F'
	else:
		unit = "K"		
	# country = city_weather['sys']['country']
	# weather_condition_main = city_weather['weather'][0]['main']
	weather_condition_descr = city_weather['weather'][0]['description']
	temp = city_weather['main']['temp']
	wind_speed = city_weather['wind']['speed']
	sunrise = city_weather['sys']['sunrise']

	tz_offset = convert_to_local(city_weather['coord'], sunrise)
	sunrise = datetime.utcfromtimestamp(sunrise+tz_offset).strftime('%d/%b/%Y %I:%M:%S%p %z')

	# convert to direction
	# wind_deg = city_weather['wind']['deg']
	print '\nToday: ' + weather_condition_descr
	print "Temperature: %.1f%s Wind speed: %.1f m/s" %(temp, unit, wind_speed)
	print "Sunrise at %s" %sunrise

def print_weather_forecast(forecast_main, result_unit):
	forecast_list = forecast_main['list']
	if result_unit == "&units=metric":
		unit = u'\xb0'
		unit = unit.encode('utf8') + 'C'
	elif result_unit == "&units=imperial":
		unit = u'\xb0'
		unit = unit.encode('utf8') + 'F'
	else:
		unit = "K"	

	tz_offset = convert_to_local(forecast_main['city']['coord'], forecast_list[0]['dt'])
	print "\nCondition:\t Date:\t\tTime:\t\tTemperature:\tWind Speed:"
	for i in range(forecast_main['cnt']):
		weather_condition_main = forecast_list[i]['weather'][0]['main']
		weather_condition_descr = forecast_list[i]['weather'][0]['description']
		temp = forecast_list[i]['main']['temp']
		wind_speed = forecast_list[i]['wind']['speed']
		forecast_time = forecast_list[i]['dt']
		forecast_time = datetime.fromtimestamp(forecast_time+tz_offset).strftime('%d/%b/%Y\t%I:%M:%S%p')
		# convert to direction
		# wind_deg = city_weather['wind']['deg']
		if i%9 == 0 and i>0:

			if len(weather_condition_descr)>=16:
				sys.stdout.write("%.16s %s\t%.1f%s\t\t%.1f m/s" %(weather_condition_descr.encode('utf-8'),forecast_time, temp, unit, wind_speed))
			else:
				sys.stdout.write("%s\t %s\t%.1f%s\t\t%.1f m/s" %(weather_condition_descr.encode('utf-8'),forecast_time, temp, unit, wind_speed))

			print_more = raw_input()
			if print_more == 'q':
				return
		else:
			if len(weather_condition_descr)>=16:
				print "%.16s %s\t%.1f%s\t\t%.1f m/s" %(weather_condition_descr.encode('utf-8'),forecast_time, temp, unit, wind_speed)
			else:
				print "%s\t %s\t%.1f%s\t\t%.1f m/s" %(weather_condition_descr.encode('utf-8'),forecast_time, temp, unit, wind_speed)				

def process_export(forecast_main):
	# import pdb
	# pdb.set_trace()
	country = forecast_main['city']['country']
	city_name = forecast_main['city']['name']
	file_timestamp = datetime.now().strftime('%Y-%m-%d-%I-%-M-%S')
	file_name = country + '_' + city_name + '_' + file_timestamp + '.csv'
	export_file = open(file_name,'w')
	export_file.write('Condition,DateTime,Temperature,Wind Speed\n')
	forecast_list = forecast_main['list']
	for i in range(forecast_main['cnt']):
		weather_condition_main = forecast_list[i]['weather'][0]['main']
		weather_condition_descr = forecast_list[i]['weather'][0]['description']
		temp = forecast_list[i]['main']['temp']
		wind_speed = forecast_list[i]['wind']['speed']
		forecast_time = forecast_list[i]['dt']
		forecast_time = datetime.fromtimestamp(forecast_time).strftime('%d/%b/%YT%H:%M:%S')
		# convert to direction
		# wind_deg = forecast_list['wind']['deg']
		if i != forecast_main['cnt']-1:
			export_file.write(weather_condition_descr.encode('utf-8')+','+forecast_time+',' + str(temp) + ',' + str(wind_speed) +'\n')
		else:
			export_file.write(weather_condition_descr.encode('utf-8')+','+forecast_time+',' + str(temp) + ',' + str(wind_speed))			

	export_file.close()

def main():
	print 'Welcome! Preparing data...'
	prepare_city_id_mapping()
	result_unit = "&units=metric"
	query_unit = string.capitalize(raw_input("Temperature result will be displayed in Celsius. Press enter to continue.\nType 'F' for Fahrenhei or 'K' for Kelvin:"))
	if query_unit != '':
		result_unit = change_unit(query_unit)

	while True:
		query_city = get_user_input('city')
		if query_city == 'Q':
			exit(0)
		city_list_dict = get_city_list(query_city)
		if city_list_dict == 'name':
			query_city = query_city.replace(' ','+')
			city_id = get_owm_city_id(query_city)
		else:
			city_id = get_city_id(city_list_dict)
		city_weather = get_city_weather(city_id, 'weather', result_unit)
		city_forecast = get_city_weather(city_id, 'forecast', result_unit)

		print_weather_current(city_weather, result_unit)

		forecast_flag = string.capitalize(raw_input("\nView forecast?[y]:"))
		if forecast_flag == 'Y':
			print_weather_forecast(city_forecast, result_unit)
			export_flag = string.capitalize(raw_input("\nExport forecast data?[y]:"))
			if export_flag == 'Y':
				process_export(city_forecast)
		print 'Thanks for using OpenWeatherMap.'

if __name__ == "__main__":
	main()
