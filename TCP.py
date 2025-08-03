import socket
import time

# 3개의 HL7 메시지 예시 (줄바꿈 없이 한 줄로)
hl7_messages = [
    "MSH|^~\&|SendingApp|SendingFac|ReceivingApp|ReceivingFac|20250409|101|ADT^A01|101|P|2.3.1| EVN|A01|20250409|F PID|1|123456|987654||d3050dc2-3c53-650c-5c965ac302b2e85e||Li^Ming|19800101|M| PV1|1|I|ICU|1|12345^Dr.John|67890^Dr.Smith|ICU&33&3293316523&4601&1|Room 101|Stable|High Priority|U| OBX|1|ST|2304^모니터이름|ICUMON1|Positive|No issues|F OBX|2|CE|2305^모니터상태|0^Active|Normal|No issues|F OBX|3|CE|4526^체온|36.5^Normal|Normal temperature|Stable|F OBX|4|CE|2307^혈압|120/80^Normal|Normal levels|No issues|F OBX|5|NM|2211^체중|70^Normal|Within healthy range|F OBX|6|NM|4524^혈당|90^Normal|Stable glucose level|F OBX|7|ST|2308^침대번호|OR01|Occupied|No issues|F OBX|8|ST|4527^환자상태|000000000000000000000000|Stable|No issues|F OBX|9|CE|4528^병실상태|16^Clean|Ready for new patient|F OBX|10|ST|4529^환자식별|005084000008|Verified|No errors|F OBX|11|CE|4530^진료상태|1^Active|Patient under observation|F OBX|12|ST|2319^환자기록|0010000150200060080610000000000000000000000000|Completed|No further issues|F",
    "MSH|^~\&|SendingApp|SendingFac|ReceivingApp|ReceivingFac|20250409|1205|ORU^R01|1205|P|2.3.1|OBX|1|ST|4523^cms_이름|JohnDoe|Patient name|Normal|F OBX|2|NM|4524^체온|36.5|Normal|Stable|F OBX|3|CE|4525^최고 alm|4^High|Excellent performance|F OBX|4|NM|4560^db 버전|12000|Latest version|Up-to-date|F OBX|5|ST|4561^일시|20181218134152|Timestamp|Valid|F",
    "MSH|^~\\& |QRY^R02|1203|P|2.3.1|QRD|20060731145557|R|I|Q895211 |RES|QRF|MON |0&0^1^1^1^|QRF|MON |0&0^3^1^1^|QRF|MON |0&0^4^1^1^|"
]

# 서버 주소와 포트 (HL7 메시지를 수신하는 서버의 주소 및 포트로 설정)
server_address = ('localhost', 12345)  # 예시: 'localhost'와 12345번 포트

# 총 30분 (1800초) 동안 실행
end_time = time.time() + 30 * 60  # 현재 시간 + 30분

# TCP 소켓 생성
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    try:
        # 서버와 연결
        sock.connect(server_address)
        
        # 메시지 전송을 30분 동안 계속 진행
        while time.time() < end_time:
            for hl7_message in hl7_messages:
                # 메시지 전송
                sock.sendall(hl7_message.encode('utf-8'))
                print(f"Sent: {hl7_message}")  # 전송한 메시지 출력
                time.sleep(10)  # 10초 대기

            # 메시지 전송이 끝나면 종료 조건을 체크
            if time.time() >= end_time:
                break  # 30분이 지났으면 종료

    except Exception as e:
        print(f"Error: {e}")
