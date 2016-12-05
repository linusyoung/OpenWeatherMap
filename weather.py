from datetime import datetime
import urllib2
import json
import string
import sys
import time

owm_apikey = '19049b9f2192b18999dc425f923ad5f4'
gtz_api_key = "AIzaSyDa7aRy4D-kIoWKaD3D1nUsRQOr_R573FU"
owm_urlbase = 'http://api.openweathermap.org/data/2.5/'
gtz_urlbase = 'https://maps.googleapis.com/maps/api/timezone/'
city_dict ={}
city_country={}

#city id mapping - moving to web server using a web call to return id

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

def get_city_list(city):
	while True:
		city_id_dict={}
		for _id, name in city_dict.items():
			if name == city:
				city_id_dict.update({city_country[_id]:_id})
		if len(city_id_dict)>0:
			return city_id_dict
		else:
			print "City is not in the list. Please try again"
			city = get_user_input('city')

def get_city_current(city_id):

	req = urllib2.Request(owm_urlbase + 'weather?id='+ str(city_id) +'&units=metric&APPID=' + owm_apikey)
	response = urllib2.urlopen(req)
	weather_data = response.read()
	weather_result = json.loads(weather_data)
	return weather_result

def get_city_forecast(city_id):
	req = urllib2.Request(owm_urlbase + 'forecast?id='+ str(city_id) +'&units=metric&APPID=' + owm_apikey)
	response = urllib2.urlopen(req)
	weather_data = response.read()
	weather_result = json.loads(weather_data)
	return weather_result

def get_user_input(choice):
	if choice == 'choice':
		chosen_city = raw_input('Please choose the city by typing the number:')
	elif choice == 'city':
		chosen_city = raw_input("Please enter a city name or 'q' to quit:\nCity name:")
		chosen_city = string.capitalize(chosen_city)

	return chosen_city

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


def print_weather_current(city_weather):
	deg = u'\xb0'
	deg = deg.encode('utf8')
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
	print "Temperature: %.1f%sC Wind speed: %.1f m/s" %(temp, deg, wind_speed)
	print "Sunrise at %s" %sunrise

def print_weather_forecast(forecast_main):
	forecast_list = forecast_main['list']
	deg = u'\xb0'
	deg = deg.encode('utf8')
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
				sys.stdout.write("%.16s %s\t%.1f%sC\t\t%.1f m/s" %(weather_condition_descr.encode('utf-8'),forecast_time, temp, deg, wind_speed))
			else:
				sys.stdout.write("%s\t %s\t%.1f%sC\t\t%.1f m/s" %(weather_condition_descr.encode('utf-8'),forecast_time, temp, deg, wind_speed))

			print_more = raw_input()
			if print_more == 'q':
				return
		else:
			if len(weather_condition_descr)>=16:
				print "%.16s %s\t%.1f%sC\t\t%.1f m/s" %(weather_condition_descr.encode('utf-8'),forecast_time, temp, deg, wind_speed)
			else:
				print "%s\t %s\t%.1f%sC\t\t%.1f m/s" %(weather_condition_descr.encode('utf-8'),forecast_time, temp, deg, wind_speed)				

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
	while True:
		chosen_city = get_user_input('city')
		if chosen_city == 'Q':
			exit(0)
		city_list = get_city_list(chosen_city)
		city_id = get_city_id(city_list)
		
		city_weather = get_city_current(city_id)
		print_weather_current(city_weather)

		forecast_flag = string.capitalize(raw_input("\nView forecast?[y]:"))
		if forecast_flag == 'Y':
			city_forecast = get_city_forecast(city_id)			
			print_weather_forecast(city_forecast)
			export_flag = string.capitalize(raw_input("\nExport forecast data?[y]:"))
			if export_flag == 'Y':
				process_export(city_forecast)
		print 'Thanks for using OpenWeatherMap.'

main()