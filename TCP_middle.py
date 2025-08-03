import socket
import time


hl7_messages = [
    "MSH|^~\\&|||||||ADT^A01|101|P|2.3.1| Mindray_Monitor|1|1000|spo2Spots|FlSpot|91^50|91|91^50",
    "MSH|^~\\&|||||||ADT^A01|101|P|2.3.1| Mindray_Monitor|1|1000|spo2Spots|FlSpot|91^50|91|91^50",
    "MSH|^~\\&|||||||ADT^A01|101|P|2.3.1| Mindray_Monitor|1|1000|heartRateSpots|FlSpot|102^30|102|102^30",
    "MSH|^~\\&|||||||ADT^A01|101|P|2.3.1| Mindray_Monitor|1|1000|breathRateSpots|FlSpot|111^30|111|111^30",
    "MSH|^~\\&|||||||ADT^A01|101|P|2.3.1| Mindray_Monitor|1|1000|spo2Spots|FlSpot|122^60|122|122^60"
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
                
                time.sleep(5)  #<-- 파라미터 설정

            # 메시지 전송이 끝나면 종료 조건을 체크
            if time.time() >= end_time:
                break  # 30분이 지났으면 종료

    except Exception as e:
        print(f"Error: {e}")
