import time
import hl7
import json
import re
import socket

# 외부 JSON 파일에서 필드 설명을 불러오기
def load_segment_meanings(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# 세그먼트 코드별 필드 설명을 매핑한 딕셔너리
segment_meanings = load_segment_meanings('segment.json')

segment_names = list(segment_meanings.keys())

# 분석 결과를 저장
analyzed_fields = []


def analyze_segment(hl7_message):
    global total_field_index  # 전역 변수 total_field_index 사용

    hl7_message = re.sub('<CR>', ' ', hl7_message)  # 공백 제거
    hl7_message = re.sub(r'\^~\\&', 'SPECIAL_SEPARATOR', hl7_message)  # 먼저 ^~\&를 임시로 치환
    hl7_message = re.sub(r'\^', ',', hl7_message)  # 나머지 ^를 ,로 치환
    hl7_message = re.sub(r'SPECIAL_SEPARATOR', '^~\\&', hl7_message)  # ^를 ,로 교체
    
    # HL7 메시지 파싱
    parsed_message = hl7.parse(hl7_message)
    total_field_index = 1  # 필드 인덱스 초기화
    
    # 각 세그먼트를 반복하며 필드 분석
    for segment in parsed_message:
        segment_code = str(segment_names)  # 세그먼트 코드 (예: MSH, EVN, PID 등)
        segment_data = str(segment[0:])  # 세그먼트 데이터 (필드들)
        
        # 세그먼트를 세그먼트 코드로 나누기
        segment_codes = "|".join(segment_names)
        
        temp = re.split(rf"({segment_codes})", segment_data)  # segment_data를 문자열로 변환
        temp = [item for item in temp if item.strip() != '']  # 빈 문자열 제거

        # 이제 각 세그먼트 코드와 데이터가 이어져 있게 됨
        temp_code = []
        for i in range(0, len(temp), 2):
            if i + 1 < len(temp):
                # 세그먼트 코드와 그 다음 세그먼트 데이터를 합침
                temp_code.append(f"{temp[i]}{temp[i + 1]}")


        # 세그먼트 코드에 맞는 필드 설명을 가져오기
        segment_description = segment_meanings.get(segment_code, {})


        # 세그먼트 코드에 맞는 필드 설명을 가져오기
        for segment_data in temp_code:
            # 세그먼트 데이터를 '|'로 나누어 필드별로 분리
            fields = segment_data.split('|')
            
            segment_code = fields[0].strip()  # 첫 번째 항목이 세그먼트 코드
            segment_description = segment_meanings.get(segment_code, {})
            
            if total_field_index == 1:
                analyzed_fields.append(f"{segment_code}")
            else:
                analyzed_fields.append(f"{segment_code}")
                total_field_index -= 1  # 세그먼트 코드와 필드 인덱스 추가
            
            # 각 필드를 순차적으로 처리
            for j, field in enumerate(fields[1:], start=1):
                field_str = field.strip()  # 앞뒤 공백 제거

                # 빈 필드도 카운트하도록 처리
                if field_str == 'F':  # HL7에서는 'F'가 빈 필드를 의미하는 경우도 있음
                    field_str = ''

                # 세그먼트 코드에서 해당 필드 번호에 대한 설명 가져오기
                field_description = segment_description.get(str(j), f"Unknown Field {j}")
                
                # 필드가 비어 있지 않다면
                if field_str:
                    analyzed_fields.append(f"{total_field_index}_{field_description}: {field_str}")
                    total_field_index += 1
                else:
                    total_field_index += 1
                    continue
                

    # 분석된 결과 출력
    log = "\n".join(analyzed_fields)
    print(log)
# 분석된 결과를 JSON 형식으로 저장
    analyzed_fields_dict = {
        "fields": analyzed_fields
    }

    # 파일이 없으면 새로운 JSON 배열을 생성하고, 있으면 기존에 데이터를 추가
    try:
        with open('analysis_results2.json', 'r', encoding='utf-8') as file:
            # 기존 데이터를 읽어 들이고, 배열로 처리
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # 파일이 없으면 빈 리스트로 시작
        data = []

    # 새로운 분석 결과 추가
    data.append(analyzed_fields_dict)

    # 분석 결과를 JSON 형식으로 파일에 저장
    with open('analysis_results2.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    return analyzed_fields


def start_server():
    server_address = ('localhost', 12345)  # 서버의 주소와 포트
    # TCP 소켓 생성
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            # 서버와 연결
            sock.bind(server_address)
            sock.listen(1)  # 클라이언트의 연결을 기다림
            print(f"Server is waiting for connections on {server_address}...")
            
            # 연결 대기
            connection, client_address = sock.accept()
            with connection:
                print(f"Connection established with {client_address}")
                
                # 클라이언트로부터 메시지를 받는 부분
                while True:
                    data = connection.recv(2048)  # 2048바이트씩 수신
                    if not data:
                        break  # 더 이상 데이터가 없으면 종료
                    hl7_message = data.decode('utf-8')  # 수신된 메시지 디코딩
                    print(f"Received: {hl7_message}")  # 수신된 메시지 출력
                    
                    # HL7 세그먼트 분석
                    analyze_segment(hl7_message)
                    
                    time.sleep(10)  # 10초 대기
        except Exception as e:
            print(f"Error: {e}")

# 메인 실행 함수
def main():
    # 서버로부터 HL7 메시지를 수신하고 분석
    start_server()

if __name__ == "__main__":
    main()
