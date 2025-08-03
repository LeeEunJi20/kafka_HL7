import time
import hl7
import json
import re
import socket
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import FastAPI, APIRouter

# FastAPI 애플리케이션 생성
app = FastAPI()

# APIRouter 객체 생성
router = APIRouter()


# 외부 JSON 파일에서 필드 설명을 불러오기
def load_segment_meanings(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# 세그먼트 코드별 필드 설명을 매핑한 딕셔너리
segment_meanings = load_segment_meanings('segment_means.json')

segment_names = list(segment_meanings.keys())

# 분석 결과를 저장
analyzed_fields = []
save_X_value = True 
time_second = 10 * 60  # 시간 설정
message_counter = 0
one_round = 5   # 데이터 개수

def analyze_segment(hl7_message):
    global total_field_index  # 전역 변수 total_field_index 사용
    global message_counter  # 전역 변수 message_counter 사용
    global save_X_value  # 전역 변수 save_X_value 사용

        
    hl7_message = re.sub('<CR>', ' ', hl7_message)  # 공백 제거
    hl7_message = re.sub(r'\^~\\&', 'SPECIAL_SEPARATOR', hl7_message)  # 먼저 ^~\&를 임시로 치환
    hl7_message = re.sub(r'\^', ',', hl7_message)  # 나머지 ^를 ,로 치환
    hl7_message = re.sub(r'SPECIAL_SEPARATOR', '^~\\&', hl7_message)  # ^를 ,로 교체
    
    # HL7 메시지 파싱
    parsed_message = hl7.parse(hl7_message)
    total_field_index = 1  # 필드 인덱스 초기화

    analyzed_fields = []
    x_value = None  #X값 초기화
    elapsed_time = 11 

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

            # MSH 세그먼트 처리
            segment_dict = {}
            for j, field in enumerate(fields[1:], start=1):
                field_str = field.strip()  # 앞뒤 공백 제거

                if field_str == 'F' or not field_str:  # 빈 필드 또는 'F'는 무시하고 넘어감
                    continue  # 빈 필드는 건너뛰고 다음 필드로 진행

                # 필드 값과 설명을 segment_dict에 추가
                field_description = segment_description.get(str(j), f"Unknown Field {j}")
                segment_dict[f"{field_description}"] = field_str
                
                if field_description == "new_value": 
                    x_value, y_value = field_str.split(',') 
                    
                    if x_value.isdigit():  # 숫자인지 확인
                        x_value = int(x_value)
                        
                        if message_counter < one_round:  # 첫 번째 주기
                            save_X_value = x_value  # x 값 그대로 사용
                            
                        else:  # 두 번째 이후부터는 1초마다 10씩 증가
                            save_X_value += time_second  # 1초마다 10씩 증가
                            x_value = save_X_value
                            
                if field_description == "new_value":
                    segment_dict["new_value"] = f"{x_value},{y_value}" 
                
                if field_description == "elapsedTime":
                    segment_dict["elapsedTime"] = x_value
                
                        
                if field_description == "metadata":
                    metadata = {}  # 새로운 setting 초기화
                    metadata['x'] = x_value
                    metadata['y'] = y_value

                    if metadata: 
                        segment_dict["metadata"] = metadata
                
            if segment_dict:  # 빈 세그먼트가 아니면
                analyzed_fields.append({segment_code: segment_dict})


    
    # 분석된 결과 출력
    log = json.dumps(analyzed_fields, ensure_ascii=False, indent=4)
    #print(log)

    # 분석된 결과를 JSON 형식으로 저장
    analyzed_fields_dict = {
        "fields": analyzed_fields
    }
    
    # 파일이 없으면 새로운 JSON 배열을 생성하고, 있으면 기존에 데이터를 추가
    try:
        with open('segment_middle_result.json', 'r', encoding='utf-8') as file:
            # 기존 데이터를 읽어 들이고, 배열로 처리
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # 파일이 없으면 빈 리스트로 시작
        data = []

    # 새로운 분석 결과 추가
    data.append(analyzed_fields_dict)
    message_counter +=1 
    # 분석 결과를 JSON 형식으로 파일에 저장
    with open('segment_middle_result.json', 'w', encoding='utf-8') as file:
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
                    #print(f"Received: {hl7_message}")  # 수신된 메시지 출력

                    analyze_segment(hl7_message)
                    
                    time.sleep(5)  # 10초 대기
        except Exception as e:
            print(f"Error: {e}")

class KafkaMessage(BaseModel):
    surgery_room_id: int
    surgery_id:int
    field_name: str
    field_type: Optional[str] = None
    new_value: Optional[Any] = None
    elapsedTime: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

# 메인 실행 함수
def main():
    # 서버로부터 HL7 메시지를 수신하고 분석
    start_server()
    for message in analyzed_fields:
        publish_message(message) 
        
@router.post("/publish-message")
def publish_message(message: KafkaMessage):
    print("Received message:", message)

    # 로그 출력 (또는 Kafka 전송 등 처리)
    print("✅ 수신된 데이터:")
    print("surgery_room_id:", message.surgery_room_id)
    print("surgery_id:", message.surgery_id)
    print("field_name:", message.field_name)
    print("field_type:", message.field_type)
    print("new_value:", message.new_value)
    print("elapsedTime:", message.elapsedTime)
    print("metadata:", message.metadata)

    # 처리 성공 응답
    return
    
if __name__ == "__main__":
    main()
