#! /usr/bin/python3

#
# Cameron Elwood
# V00152812
# CSC 361 Assignment 1: SmartClient.py
#


import sys
import socket
import ssl
import re

name = sys.argv[1]
nameOrig = name


def testHTTP2(name):
	#some code taken from https://python-hyper.org/projects/h2/en/stable/negotiating-http2.html
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		con = (name, 443)
		sock.connect(con)
	except:
		print("Error connecting to the host: "+name)


	ctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
	ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")


	whichProt = 0
	try:
		whichProt = 3
		ctx.set_alpn_protocols(["h2", "http/1.1"])
	except NotImplementedError:
		pass

	try:
		if whichProt == 0:
			whichProt = 2
		ctx.set_npn_protocols(["h2", "http/1.1"])
	except NotImplementedError:
		if whichProt == 3:
			whichProt = 1

	suSock = ctx.wrap_socket(sock, server_hostname = name)
	neg_prot = None

	if whichProt == 1 | whichProt == 3:
		neg_prot = suSock.selected_alpn_protocol()
	if (whichProt == 2 | whichProt == 3) and neg_prot==None:
		neg_prot = suSock.selected_npn_protocol()

	if neg_prot == "h2":
		return True
	else:
		return False


def getCookies(val):
	newWins = re.findall(r"Set-Cookie: ([^=]*?)=(?!deleted).*?(?:domain=(.*?\.c[oa]m?)(.*)?)?\r\n", val)
	#newWins = re.findall(r"Set-Cookie: ([^=]*?)=(?!deleted).*?", val)
	#newWins2 = re.findall(r"Set-Cookie: .*; (?:domain=(.*?\.c[oa]m?)(.*)?)?\r\n", val)
	cooks = []
	for i in newWins:
		domain = ''
		if i[1] == '':
			domain = '-'
		else:
			domain = i[1]
		cooks.append("name: -, key: "+i[0]+', domain name: '+domain)
	return cooks
	



#if the website does not support https, we need to send them a message again with a socket that is not wrapped in ssl

check = True
httpsBool = True
version = '1.1'
numSock= 443
name2 ='/'
while True:
	try:
		ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except:
		print("Could not connect")
		sys.exit()
	#can skip this line if its not suppose to have ssl enabled
	if check:
		ss = ssl.wrap_socket(ss, ssl_version=ssl.PROTOCOL_TLSv1)
	try:
		ip_addr = socket.gethostbyname(name);
	except:
		print("Could not connect to "+name)
		sys.exit()


	addr = (ip_addr, numSock)
	try:
		ss.connect(addr) #can be done with a regular socket
	except:
		print("could not connect to :" +name)
		sys.exit()
	try:
		message = 'GET '+name2+' HTTP/'+version+'\r\nHost:' + name +'\r\n\r\n'
		message = message.encode()
		ss.send(message) #can be done with a regular socket
	except:
		print("error with sening message. Message: " + message)
		sys.exit()

	try:
		resp = ss.recv(4096) #can be done with a regular socket
		val = resp.decode("utf-8")
		found = re.search(r'((1|2|3|4|5)\d\d)', val, flags=0)
		val2 = found.group(1)
		num = found.group(2)
	except:
		print("error with message recieved: " + val)
		sys.exit()

	if num == "1":
		print("100 error: "+val) #wierd error probably wont ever happen
		break
	if num == "2":

		print("website: "+name)
		what = False
		try:
			what = testHTTP2(name)
			if what:
				version = '2'
		except:
			pass
		print("1. Supports HTTPS: " + str(httpsBool))
		print("2. The newest HTTP versions that the web server supports: HTTP/"+version)
		cookies = getCookies(val) #successful return
		print("3. List of Cookies:")
		for i in cookies:
			print(i)
		break
	if num == "3":
		found2 = re.search(r'[Ll]ocation: (http(s)?:\/\/(.*?))\/?\r\n', val, flags=0) #warning, permenant 
		if(found2.group(3) == name):
			if(found2.group(2)!='s'):
				httpsBool = False
			check = False
			numSock= 80
			ss.close()
			continue
		
		name2= found2.group(1)
		continue
	if num == "4": #invalid request, client error
		print(message)
		print("400 error: "+val)
		break
	if num == "5": #server error, valid request
		if(version=='1.0'):
			print("500 error: "+val)
			break;
		#if we go here, that means its http 1.0
		version = '1.0'
		continue
