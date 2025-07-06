import socket
import os
import struct
import time
import select

# ICMP报文类型：请求
ICMP_TYPE_REQUEST = 8
ICMP_CODE_REQUEST_DEFAULT = 0
# ICMP报文类型：应答
ICMP_TYPE_REPLY = 0
ICMP_CODE_REPLY_DEFAULT = 0
# ICMP报文类型：超时
ICMP_TYPE_TIMEOUT = 11
ICMP_CODE_TTL_TIMEOUT = 0
# ICMP报文类型：不可达
ICMP_TYPE_UNREACHABLE = 3

MAX_HOPS = 30  # 最大跳数限制
TRIES = 3  # 探测尝试次数
TIMEOUT = 2  # 超时时间设置为2秒


# 计算校验和
def calculate_checksum(data):
    checksum = 0
    count_to = (len(data) // 2) * 2
    count = 0
    while count < count_to:
        this_val = data[count + 1] * 256 + data[count]
        checksum += this_val
        checksum = checksum & 0xffffffff
        count += 2
    if count_to < len(data):
        checksum += data[len(data) - 1]
        checksum = checksum & 0xffffffff
    checksum = (checksum >> 16) + (checksum & 0xffff)
    checksum = checksum + (checksum >> 16)
    answer = ~checksum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


# 获取主机信息
def get_host_info(host_addr):
    try:
        host_info = socket.gethostbyaddr(host_addr)
    except socket.error:
        display = '{0}'.format(host_addr)
    else:
        display = '{0} ({1})'.format(host_addr, host_info[0])
    return display


# 构建ICMP数据包
def build_icmp_packet():
    # 初始校验和
    checksum = 0
    # 进程ID
    process_id = os.getpid()
    # 序列号设为1(>0)
    sequence_number = 1
    # 构建ICMP头部
    icmp_header = struct.pack("bbHHh", ICMP_TYPE_REQUEST, ICMP_CODE_REQUEST_DEFAULT, checksum, process_id,
                              sequence_number)
    # 当前时间戳作为负载
    timestamp_data = struct.pack("d", time.time())
    # 拼接数据包
    packet = icmp_header + timestamp_data
    # 计算校验和
    checksum = calculate_checksum(packet)
    # 小端转大端
    checksum = socket.htons(checksum)
    # 重新构建头部
    icmp_header = struct.pack("bbHHh", ICMP_TYPE_REQUEST, ICMP_CODE_REQUEST_DEFAULT, checksum, process_id, 1)
    # 构建完整的数据包
    icmp_packet = icmp_header + timestamp_data
    return icmp_packet


def trace_route(hostname):
    print(f"正在追踪 {hostname}[{socket.gethostbyname(hostname)}]（最大跳数 = {MAX_HOPS}，探测尝试次数 = {TRIES}）")
    for ttl in range(1, MAX_HOPS):
        print(f"{ttl:2d}", end="")
        for tries in range(TRIES):
            # 创建原始套接字
            icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
            icmp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
            icmp_socket.settimeout(TIMEOUT)
            # 构建ICMP数据包
            icmp_packet = build_icmp_packet()
            icmp_socket.sendto(icmp_packet, (hostname, 0))
            # 等待接收回复
            start_time = time.time()
            select.select([icmp_socket], [], [], TIMEOUT)
            end_time = time.time()
            # 计算接收时间
            receive_time = end_time - start_time
            if receive_time >= TIMEOUT or receive_time == 0:
                print("    *    ", end="")
            else:
                print(f" {receive_time * 1000:4.0f} ms ", end="")
            if tries >= TRIES - 1:
                try:
                    ip_packet, ip_info = icmp_socket.recvfrom(1024)
                except socket.timeout:
                    print(" 请求超时")
                else:
                    # 从IP数据包中提取ICMP头
                    icmp_header = ip_packet[20:28]
                    # 拆包ICMP头
                    after_type, _, _, _, _ = struct.unpack("bbHHh",icmp_header)
                    output = get_host_info(ip_info[0])
                    if after_type == ICMP_TYPE_UNREACHABLE:  # 不可达
                        print("错误！网络/主机/端口不可达！")
                        break
                    elif after_type == ICMP_TYPE_TIMEOUT:  # TTL超时
                        print(f" {output}")
                        continue
                    elif after_type == ICMP_TYPE_REPLY:  # 类型为回复
                        print(f" {output}")
                        print("程序运行结束！")
                        return
                    else:
                        print("请求超时")
                        print("程序运行错误！")
                        return


if __name__ == "__main__":
    while True:
        try:
            target_ip = input("请输入目标IP地址：")
            TIMEOUT = int(input("请输入超时时间（秒）："))
            trace_route(target_ip)
            break
        except Exception as e:
            print(e)
            continue
