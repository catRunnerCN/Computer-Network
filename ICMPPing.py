import socket
import os
import struct
import time
import select

# ICMP报文类型
ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0
ICMP_DEST_UNREACH = 3
ICMP_NET_UNREACH = 0
ICMP_HOST_UNREACH = 1
ByteOrder = "!bbHHh"


# 计算校验和


def checksum(data):
    n = len(data)
    m = n % 2
    sum1 = 0
    for i in range(0, n - m, 2):
        sum1 += (data[i]) + ((data[i + 1]) << 8)
    if m:
        sum1 += (data[-1])
    sum1 = (sum1 >> 16) + (sum1 & 0xffff)
    sum1 += (sum1 >> 16)
    answer = ~sum1 & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


# 接收一个Ping的回复
def receive_one_ping(my_socket, id_rec, sequence, timeout):
    time_left = timeout
    seq = sequence
    while True:
        started_select = time.time()
        what_ready = select.select([my_socket], [], [], time_left)
        how_long_in_select = (time.time() - started_select)
        if not what_ready[0]:  # 超时
            return None, None

        time_received = time.time()
        rec_packet, _ = my_socket.recvfrom(1024)

        # 解析ICMP头部
        header = rec_packet[20:28]
        type_prot, code, _, packet_id, _ = struct.unpack(ByteOrder, header)
        print(code, type_prot)
        if type_prot == 0 and packet_id == id_rec:  # 类型应为0
            delay = time_received - started_select
            ttl = struct.unpack("!b", rec_packet[8:9])[0]
            return delay, ttl
        elif type_prot == 3:
            if code == 1:
                print("目标主机不可达。", seq)
            elif code == 2:
                print("目标网络不可达。")
            else:
                print("由于其他原因目标不可达。")

        time_left = time_left - how_long_in_select
        if time_left <= 0:
            return None, None


# 发送一个Ping请求
def send_one_ping(my_socket, id_rece, sequence, dest_addr):
    my_check_sum = 0
    header = struct.pack(ByteOrder, ICMP_ECHO_REQUEST, 0, my_check_sum, id_rece, sequence)
    data = struct.pack("!d", time.time())
    my_check_sum = checksum(header + data)
    header = struct.pack(ByteOrder, ICMP_ECHO_REQUEST, 0, my_check_sum, id_rece, sequence)
    packet = header + data
    my_socket.sendto(packet, (dest_addr, 1))


# 执行一次Ping操作
def do_one_ping(dest_addr, id_rece, sequence, timeout):
    icmp = socket.getprotobyname("icmp")
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    send_one_ping(my_socket, id_rece, sequence, dest_addr)
    delay, ttl = receive_one_ping(my_socket, id_rece, sequence, timeout)
    my_socket.close()
    return delay, ttl


# 执行Ping命令
def ping(host, timeout=1, count=4):
    try:
        dest = socket.gethostbyname(host)
    except socket.gaierror:
        print("无法解析主机名: " + host)
        return

    print("使用Python正在Ping " + dest + "：")
    print("")
    my_id = os.getpid() & 0xFFFF
    loss = 0
    delays = []
    for i in range(count):
        result, ttl = do_one_ping(dest, my_id, i, timeout)
        if not result:
            print("请求超时。")
            loss += 1
        else:
            delay = int(result * 1000)
            delays.append(delay)
            print("从 " + dest + " 接收到：" + "字节=" + str(ttl) + " 延迟=" + str(delay) + "ms TTL=" + str(ttl))
        time.sleep(1)
    print("数据包：发送 = " + str(count) + " 接收 = " + str(count - loss) + " 丢失 = " + str(loss))
    if delays:
        print("最小延迟 = {}ms，最大延迟 = {}ms，平均延迟 = {}ms".format(min(delays), max(delays), sum(delays) // len(delays)))


# 用户输入
ping(input("请输入您要Ping的网站: "), timeout=int(input("请输入时间允许: ")), count=int(input("请输入Ping次数: ")))
