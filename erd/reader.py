# erd/reader.py
import os
import sys
import glob
import re
import importlib
from typing import Optional, Any
from loguru import logger

def setup_python_path(project_root: str) -> str:
    """
    [함수의 역할] 모듈 탐색이 원활하게 진행될 수 있도록 프로젝트 루트 및 그 상위 디렉토리를 sys.path에 동적으로 등록합니다.
    [상태 변경 및 사이드 이펙트] sys.path 리스트에 새로운 경로들을 추가하여 파이썬 런타임의 임포트 경로 환경을 변경합니다.
    [결과 반환] 임포트 경로 변환의 기준이 되는 parent_dir 경로 반환
    """
    parent_dir = os.path.dirname(project_root)
    # [제어 흐름 및 비즈니스 분기] 동일한 경로가 이미 sys.path에 등록되어 중복 삽입되는 것을 방지하기 위해 존재 여부 사전 분기 검사
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    return parent_dir

def _get_module_path(file_path: str, parent_dir: str) -> str:
    """
    [함수의 역할] 물리 파일 경로를 파이썬의 점(.) 구분자 기반 패키지 모듈 경로로 변환합니다.
    [데이터 변환] 파일 절대 경로에서 parent_dir 기준의 상대 경로를 계산한 뒤 슬래시를 점으로 변경
    [결과 반환] 변환된 파이썬 모듈 경로 명칭
    """
    relative_path = os.path.relpath(file_path, parent_dir)
    return os.path.splitext(relative_path)[0].replace(os.path.sep, ".")

def discover_base_class(project_root: str, parent_dir: str) -> Optional[Any]:
    """
    [함수의 역할] 프로젝트 내에서 SQLAlchemy declarative base(Base 객체)가 정의된 모듈을 검색하고 동적으로 임포트하여 반환합니다.
    [데이터 I/O] 디스크 내의 파이썬 파일들을 읽어 텍스트 분석 수행
    [데이터 필터] 정규식을 통해 declarative base를 선언하는 패턴을 필터링 및 매칭
    [결과 반환] 임포트 성공 시 Base 클래스 또는 MetaData 객체를 반환하고, 실패 시 None을 반환
    """
    py_files = glob.glob(os.path.join(project_root, "**", "*.py"), recursive=True)
    base_patterns = [
        re.compile(r"(\w+)\s*=\s*(?:declarative_base|generate_base)\("),
        re.compile(r"class\s+(\w+)\s*\(\s*DeclarativeBase\s*\)"),
        re.compile(r"(\w+)\s*=\s*SQLAlchemy\(")
    ]
    
    candidates = []
    # [제어 흐름 및 비즈니스 분기] 프로젝트 내의 모든 파이썬 파일을 순회하여 Base 선언부를 탐색
    for file_path in py_files:
        if "erd" in file_path or "test_generate_erd" in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # [제어 흐름 및 비즈니스 분기] 파일 본문에서 정의된 패턴을 찾아 매칭 시도
            for pattern in base_patterns:
                match = pattern.search(content)
                if match:
                    base_var_name = match.group(1)
                    module_path = _get_module_path(file_path, parent_dir)
                    try:
                        module = importlib.import_module(module_path)
                        base_obj = getattr(module, base_var_name, None)
                        if base_obj is not None and (hasattr(base_obj, "metadata") or hasattr(base_obj, "tables")):
                            metadata = base_obj.metadata if hasattr(base_obj, "metadata") else base_obj
                            # [제어 흐름 및 비즈니스 분기] 이미 테이블이 성공적으로 매핑되어 활성화된 Base 객체라면 최우선으로 즉시 선택
                            if metadata and metadata.tables:
                                logger.info(f"Discovered active Base '{base_var_name}' with registered tables in module '{module_path}'")
                                return base_obj
                            candidates.append(base_obj)
                    except Exception as e:
                        logger.debug(f"Failed to import candidate {module_path}: {e}")
        except Exception as e:
            logger.debug(f"Failed to read file {file_path} for base discovery: {e}")
            
    # [제어 흐름 및 비즈니스 분기] 테이블이 매핑된 활성 Base를 최종 찾지 못한 경우, 수집된 후보 중 첫 번째 Base로 폴백 선택
    if candidates:
        logger.info("No active Base with registered tables found. Using the first discovered candidate.")
        return candidates[0]
    return None

def auto_import_models(project_root: str, parent_dir: str, file_pattern: str) -> None:
    """
    [함수의 역할] 프로젝트 내에서 모델 정의 파일들을 찾아 동적으로 로드하여 SQLAlchemy Base 메타데이터에 등록시킵니다.
    [데이터 I/O] 지정된 파일 패턴에 부합하는 모델 파일을 디스크에서 검색
    [데이터 변환] 파일 경로를 파이썬 모듈 경로로 치환
    """
    model_files = glob.glob(os.path.join(project_root, "**", file_pattern), recursive=True)
    logger.info(f"Found {len(model_files)} model files using pattern '{file_pattern}'.")
    
    # [제어 흐름 및 비즈니스 분기] 찾아진 모델 파일들을 순회하며 importlib을 통해 개별 모듈 로드 수행
    for model_file_path in model_files:
        module_path = _get_module_path(model_file_path, parent_dir)
        try:
            importlib.import_module(module_path)
            logger.info(f"Successfully loaded and registered: {module_path}")
        except Exception as e:
            logger.error(f"Failed to import module {module_path}: {e}")

def get_metadata(base_obj: Any) -> Optional[Any]:
    """
    [함수의 역할] Base 객체로부터 SQLAlchemy MetaData 인스턴스를 추출합니다.
    [결과 반환] MetaData 객체가 존재하면 반환하고, 없을 경우 None을 반환
    """
    if hasattr(base_obj, "metadata"):
        return base_obj.metadata
    if hasattr(base_obj, "tables"):
        return base_obj
    return None

def validate_metadata(metadata: Any) -> bool:
    """
    [함수의 역할] SQLAlchemy MetaData 안에 시각화 또는 스키마 생성에 필요한 테이블이 정의되어 있는지 검증합니다.
    [결과 반환] 하나 이상의 테이블이 메타데이터에 성공적으로 등록되어 있으면 True, 비어 있다면 False를 리턴합니다.
    """
    if not metadata or not metadata.tables:
        logger.warning("No database tables registered in metadata. Please check model definitions.")
        return False
    return True

def read_firestore_metadata(project_root: str) -> dict[str, list[tuple[str, str]]]:
    """
    [함수의 역할] 프로젝트 소스코드를 분석하여 파이어스토어 컬렉션명과 각 문서 스펙 필드/타입 정보를 추출합니다.
    [데이터 I/O] 디스크 내의 파이썬 파일 목록을 스캔하고 텍스트 파일을 조회합니다.
    [데이터 필터] 정규식을 통해 파이어스토어 컬렉션 정의(.collection(...)) 및 DTO 스키마 필드 매칭 검출
    [결과 반환] 컬렉션명과 필드 정보 목록이 매핑된 딕셔너리 구조
    """
    logger.info(f"Scanning project for Firestore collections at: {project_root}")
    collections: dict[str, list[tuple[str, str]]] = {}
    py_files = glob.glob(os.path.join(project_root, "**", "*.py"), recursive=True)
    collection_pattern = re.compile(r'\.collection\("([^"]+)"\)')
    
    # [제어 흐름 및 비즈니스 분기] 프로젝트의 파이썬 파일들을 순회하며 파이어스토어 컬렉션 접근 코드를 탐색
    for file_path in py_files:
        if "erd" in file_path or "test_generate_erd" in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            matches = collection_pattern.findall(content)
            # [제어 흐름 및 비즈니스 분기] 파일 내에서 파이어스토어 컬렉션 명칭을 찾은 경우 스키마 분석 진행
            for col_name in matches:
                if col_name not in collections:
                    collections[col_name] = []
                    
                    dir_path = os.path.dirname(file_path)
                    schema_file = os.path.join(dir_path, "schemas.py")
                    
                    # [제어 흐름 및 비즈니스 분기] schemas.py 파일이 있는 경우 Pydantic 모델 파싱 시도
                    if os.path.exists(schema_file):
                        with open(schema_file, "r", encoding="utf-8") as sf:
                            s_content = sf.read()
                        
                        words = "".join([w.capitalize() for w in col_name.split("_") if w != "post"])
                        words_singular = words[:-1] if words.endswith("s") else words
                        
                        class_pattern = re.compile(
                            rf"class\s+({words_singular}\w*Response|{words_singular}\w*Create)\s*\(\s*BaseModel\s*\):([\s\S]*?)(?=class|\Z)"
                        )
                        class_matches = class_pattern.findall(s_content)
                        
                        # [제어 흐름 및 비즈니스 분기] 일치하는 DTO 클래스를 찾은 경우 내부 필드와 타입을 추출하여 기록
                        for class_name, class_body in class_matches:
                            field_pattern = re.compile(r"^\s+(\w+)\s*:\s*(\w+)", re.MULTILINE)
                            fields = field_pattern.findall(class_body)
                            for f_name, f_type in fields:
                                if (f_name, f_type) not in collections[col_name]:
                                    collections[col_name].append((f_name, f_type))
        except Exception as e:
            logger.debug(f"Failed to scan file {file_path} for Firestore: {e}")
            
    # [제어 흐름 및 비즈니스 분기] 동적 탐색 실패 시 빈 결과를 반환하고 처리를 종료
    if not collections:
        logger.warning("No Firestore collections found dynamically.")
    return collections
