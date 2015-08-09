import sys
import os
import binascii
import struct
import socket
import yaml

vldb_lst_size = 141376
number_of_servers = 0
max_servers = 252

def create_data():
	vldb_lst = [0] * vldb_lst_size
	return vldb_lst

def init_ubik_header(vldb_lst):
	vldb_lst[1] = 0x35
	vldb_lst[2] = 0x45
	vldb_lst[3] = 0x45
	vldb_lst[7] = 0x40
	vldb_lst[67] = 0x04

def add_mh_ref(vldb_lst):
	global number_of_servers
	n_servers = 0
	vldb_lst[132181] = vldb_lst[132497] = 0x02
	vldb_lst[132182] = vldb_lst[132498] = 0x05
	vldb_lst[132183] = vldb_lst[132499] = 0x40
	vldb_lst[132495] = 0x08
	for i in range(0, 4):
		for j in range(1, 64):
			vldb_lst[104 + n_servers * 4] = 0xff
			vldb_lst[105 + n_servers * 4] = hex(i)[2:].zfill(2).decode('hex')
			vldb_lst[107 + n_servers * 4] = hex(j)[2:].zfill(2).decode('hex')
			n_servers += 1
			if n_servers == number_of_servers or n_servers == max_servers:
				number_of_servers = n_servers
				vldb_lst[132483] = hex(n_servers)[2:].zfill(2).decode('hex')
				return

def add_uuid(vldb_lst, i, uuid):
	uuid_lst = uuid.split()
	uuid_hex = []
	for element in uuid_lst:
		uuid_hex.append(element[:2])
		uuid_hex.append(element[2:])
	for j in range(0, 16):
		vldb_lst[(132608 + i * 128) + j] = binascii.a2b_hex(str(uuid_hex[j]).zfill(2))

def add_ip_addr(vldb_lst, ip_addr, k, w):
	ip = hex(struct.unpack('!I', socket.inet_aton(ip_addr))[0])
	ip_hex = ip[2:]
	ip_lst = [ip_hex[i : i + 2] for i in range(0, len(ip_hex), 2)]
	for i in range(0, 5):
		vldb_lst[132627 + k * 128] = 0x01
		for j in range(0, 4):
			vldb_lst[132628 + j + (k * 128) + (4 * w)] = binascii.a2b_hex(str(ip_lst[j]).zfill(2))

def add_mh_entry(vldb_lst, conf):
	for i in range(0, number_of_servers):
		j = 0
		add_uuid(vldb_lst, i, conf['server_' + str(i + 1)]['uuid'])
		for key in conf['server_' + str(i + 1)]['addrs']:
			add_ip_addr(vldb_lst, conf['server_' + str(i + 1)]['addrs'][key], i, j)
			j += 1
			if j == 15:
				break

def add_servers(vldb_lst, conf):
	add_mh_ref(vldb_lst)
	add_mh_entry(vldb_lst, conf)

def save_data(vldb_lst, output):
	with file(output, 'wb') as fd:
		bytes = bytearray(vldb_lst)
		fd.write(bytes)

if __name__ == '__main__':
	if len(sys.argv) < 3:
		sys.exit('Usage: python %s <conf-path> <output-path>' % sys.argv[0])
	if not os.path.exists(sys.argv[1]):
		sys.exit('ERROR: The configuration file %s was not found!' % sys.argv[1])
	with open(sys.argv[1], 'r') as f:
		conf = yaml.load(f)
	number_of_servers = int(conf['num_server'])
	vldb_lst = create_data()
	init_ubik_header(vldb_lst)
	add_servers(vldb_lst, conf)
	save_data(vldb_lst, sys.argv[2])