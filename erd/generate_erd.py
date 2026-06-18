# erd/generate_erd.py
import argparse
import importlib
import os
import sys
from typing import Callable, Optional, Any

from loguru import logger
from sqlalchemy import create_mock_engine
import reader

# [비직관적인 최적화 및 우회 코드]
# Windows 환경에서 시스템에 Graphviz가 설치되어 있음에도 PATH에 자동 반영되지 않아
# eralchemy2 구동에 실패하는 이슈를 해결하기 위해 일반 설치 경로 후보들을 찾아 PATH에 주입합니다.
def setup_graphviz_path() -> None:
    """
    [함수의 역할] Windows 환경에서 Graphviz가 설치된 경로를 탐색하여 PATH 환경 변수에 추가합니다.
    [상태 변경 및 사이드 이펙트] os.environ["PATH"]에 Graphviz 경로를 추가하여 전체 프로세스의 PATH 상태를 수정합니다.
    """
    if os.name != "nt":
        return
    possible_paths = [
        r"C:\Program Files\Graphviz\bin",
        r"C:\Program Files (x86)\Graphviz\bin",
    ]
    # [제어 흐름 및 비즈니스 분기] 복수의 가능한 설치 경로를 순회하며 실제 존재하는 경로를 찾아 PATH에 주입하기 위해 순회
    for path in possible_paths:
        if os.path.exists(path) and path not in os.environ.get("PATH", ""):
            os.environ["PATH"] += os.pathsep + path
            logger.info(f"Graphviz path added to PATH: {path}")
            break

# Graphviz PATH 설정을 먼저 수행하여 eralchemy2(pygraphviz) 임포트 시 DLL 로드 실패를 미연에 방지합니다.
setup_graphviz_path()

from eralchemy2 import render_er

# [비직관적인 최적화 및 우회 코드]
# aiosqlite가 설치되지 않은 환경(예: 개발자의 전역 파이썬 런타임)에서도
# 모델 파일 로드 시 데이터베이스 커넥션 생성(create_async_engine)이 실패하지 않도록
# aiosqlite 모듈을 가상(Mock)으로 주입하여 Graceful Degradation을 보장합니다.
try:
    import aiosqlite
except ImportError:
    from unittest.mock import MagicMock
    mock_aiosqlite = MagicMock()
    mock_aiosqlite.sqlite_version_info = (3, 40, 0)
    sys.modules["aiosqlite"] = mock_aiosqlite


# [비직관적인 최적화 및 우회 코드]
# erd 디렉토리를 백엔드 환경 어디에 붙여넣어도 reader 모듈을 바로 찾아서 임포트할 수 있도록,
# 스크립트 실행 디렉토리를 sys.path 최상단에 주입합니다.
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# [비직관적인 최적화 및 우회 코드]
# 모델 임포트 시 데이터베이스 설정 검증(Fail-Fast)으로 인해 스크립트가 비정상 종료되는 것을 방지하기 위해,
# 런타임에 모의(Mock) 환경변수 또는 테스트 플래그를 사전에 주입합니다.
# 또한, 드라이버 미설치 오류를 피하기 위해 기본 내장/설치된 sqlite+aiosqlite를 기본값으로 설정합니다.
os.environ.setdefault("TESTING", "True")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

def _save_file(output_path: str, content: str) -> bool:
    """
    [함수의 역할] 텍스트 형식의 스키마 및 다이어그램 결과물을 파일로 저장합니다.
    [데이터 I/O] 디스크에 텍스트 인코딩을 적용해 파일 작성
    [결과 반환] 파일 쓰기 성공 시 True, 실패 및 에러 발생 시 False 리턴
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Failed to save file {output_path}: {e}")
        return False

def generate_sql_ddl(metadata: Any, output_path: str = "erd.sql") -> bool:
    """
    [함수의 역할] erdcloud 등에서 임포트하여 ERD 시각화가 가능한 표준 SQL DDL 문(PostgreSQL 규격)을 생성합니다.
    [데이터 변환] SQLAlchemy Base 메타데이터를 표준 DDL SQL 쿼리 목록으로 컴파일
    [데이터 I/O] 생성된 DDL SQL 쿼리를 디스크 파일로 저장
    [결과 반환] 성공 여부 (boolean)
    """
    try:
        # [제어 흐름 및 비즈니스 분기] 메타데이터가 등록되지 않은 상태에서 컴파일 진행 시 빈 파일이 생성되는 문제를 조기 방지하기 위해 분기
        if not reader.validate_metadata(metadata):
            return False
        
        logger.info(f"Generating SQL DDL (PostgreSQL Dialect) at: {output_path}")
        statements: list[str] = [
            "-- Database DDL SQL Schema",
            "-- Created dynamically from SQLAlchemy Metadata",
            "-- Compatible with erdcloud import\n"
        ]

        def executor(sql: str, *args, **kwargs) -> None:
            sql_str: str = str(sql).strip()
            # [데이터 필터] 빈 SQL DDL 선언문이 어펜드되어 세미콜론이 홀로 누적되는 오염을 걸러내기 위해 빈 문자열 필터링 분기
            if sql_str:
                statements.append(sql_str + ";")

        # PostgreSQL 규격으로 DDL 쿼리 빌드
        engine = create_mock_engine("postgresql://", executor)
        metadata.create_all(engine)

        content: str = "\n\n".join(statements)
        return _save_file(output_path, content)
    except Exception as e:
        logger.error(f"Failed to generate SQL DDL: {e}")
        return False

def generate_png_erd(base_obj: Any, output_path: str = "erd.png") -> bool:
    """
    [함수의 역할] eralchemy2를 사용하여 png 이미지 다이어그램을 출력합니다.
    [멀티 라이브러리 연동] SQLAlchemy metadata 스키마 객체와 eralchemy2의 렌더 엔진을 연동하여 이미지 생성
    [데이터 I/O] 렌더링된 바이너리 이미지 데이터 파일을 디스크에 물리적으로 기록
    [결과 반환] 성공 여부 리턴 (boolean)
    """
    try:
        metadata = reader.get_metadata(base_obj)
        # [제어 흐름 및 비즈니스 분기] 컴파일할 테이블 정보가 없을 경우 렌더러 구동 이전에 조기 거절하기 위해 분기
        if not reader.validate_metadata(metadata):
            return False
            
        logger.info(f"Generating Image ERD diagram using eralchemy2 at: {output_path}")
        render_er(base_obj, output_path)
        logger.info(f"Image ERD successfully generated at: {output_path}")
        return True
    except Exception as e:
        # [비직관적인 최적화 및 우회 코드]
        # Graphviz 미설치 시 에러를 던지지 않고 경고 로그만 남겨 다른 DDL 생성 흐름에 지장을 주지 않도록 합니다 (Graceful Degradation).
        logger.warning(f"Could not generate PNG ERD (Graphviz/eralchemy2 missing or compilation error). Details: {e}")
        return False

def generate_firestore_erd(project_root: str, output_path: str) -> bool:
    """
    [함수의 역할] 프로젝트 소스코드를 분석하여 파이어스토어 컬렉션과 필드 구조를 추출하고, Mermaid Flowchart 형식의 마크다운 파일을 생성합니다.
    [데이터 I/O] reader 모듈을 사용하여 디스크 파일들로부터 파이어스토어 메타데이터 정보를 받아옵니다.
    [데이터 변환] 파이어스토어 컬렉션 명칭 및 스키마 필드 정보를 Mermaid Flowchart 다이어그램 문자열로 변환합니다.
    [데이터 I/O] 작성된 Mermaid 다이어그램 텍스트를 디스크 파일로 기록합니다.
    [결과 반환] 생성 성공 시 True, 실패 시 False 반환
    """
    try:
        # [데이터 I/O] reader를 통해 파이어스토어 컬렉션 메타데이터 수집
        collections = reader.read_firestore_metadata(project_root)
        
        # [제어 흐름 및 비즈니스 분기] 감지된 파이어스토어 컬렉션이 없는 경우, 생성을 진행하지 않고 중단합니다.
        if not collections:
            logger.warning("No Firestore collections detected. Skipping Firestore ERD generation.")
            return False
            
        logger.info(f"Generating Firestore ERD flowchart at: {output_path}")
        lines = [
            "# Firebase Firestore Entity Relationship Diagram (ERD)\n",
            "```mermaid",
            "flowchart TD",
            "    subgraph Firestore [\"Firebase Firestore DB\"]"
        ]
        
        # [제어 흐름 및 비즈니스 분기] 수집된 파이어스토어 컬렉션과 필드 목록들을 Mermaid 문법으로 직렬화하기 위해 컬럼과 문서별 순회
        for idx, (col_name, fields) in enumerate(collections.items()):
            col_id = f"col_{idx}"
            lines.append(f"        subgraph {col_id} [\"Collection: {col_name}\"]")
            # [제어 흐름 및 비즈니스 분기] 각 컬럼 필드를 루프 돌며 노드 맵 어펜드
            for f_idx, (f_name, f_type) in enumerate(fields):
                field_id = f"{col_id}_f{f_idx}"
                lines.append(f"            {field_id}[\"{f_name} ({f_type})\"]")
            lines.append("        end")
        lines.append("    end")
        lines.append("```\n")
        
        return _save_file(output_path, "\n".join(lines))
    except Exception as e:
        logger.error(f"Failed to generate Firestore ERD: {e}")
        return False

def parse_arguments() -> argparse.Namespace:
    """
    [함수의 역할] 명령줄(CLI)로 전달된 프로젝트 루트, Base 클래스 경로, 모델 파일 매칭 패턴 등을 파싱합니다.
    [결과 반환] CLI 매개변수들이 바인딩된 Namespace 객체를 리턴합니다.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_root = os.path.abspath(os.path.join(script_dir, ".."))
    
    parser = argparse.ArgumentParser(description="Generalized Database ERD and DDL generator")
    parser.add_argument("output", type=str, nargs="?", default="all", help="Output file path/format (e.g. erd.png, erd.sql, firestore_erd.md) or 'all'")
    parser.add_argument("--root", type=str, default=default_root, help="Root directory of the project containing models")
    parser.add_argument("--base", type=str, default=None, help="Import path for SQLAlchemy Base (e.g. app.db.base:Base)")
    parser.add_argument("--pattern", type=str, default="*model*.py", help="Glob pattern for model files (e.g. *model.py)")
    return parser.parse_args()

def _resolve_output_path(output_path: str, script_dir: str) -> str:
    """
    [함수의 역할] 출력 파일명 또는 확장자가 상대 경로일 때, erd/ 디렉토리 경로에 맵핑하여 물리적 위치를 보장합니다.
    [결과 반환] 변환된 절대 경로 문자열
    """
    # [제어 흐름 및 비즈니스 분기] 절대 경로가 아닌 경우에 한하여 erd 디렉토리 내부 경로로 강제 주입
    if not os.path.isabs(output_path):
        return os.path.join(script_dir, output_path)
    return output_path

def main() -> None:
    """
    [함수의 역할] 전체 실행 제어 흐름을 조율하고, Base 검색, 모델 로드, SQL/PNG/Mermaid 생성을 실행합니다.
    """
    args = parse_arguments()
    project_root = os.path.abspath(args.root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    setup_graphviz_path()
    parent_dir = reader.setup_python_path(project_root)
    
    # [상태 변경 및 사이드 이펙트] 프로젝트 내의 모든 모델 파일들을 먼저 로드하여 해당 테이블들이 각 Base 메타데이터에 등록되도록 만듭니다.
    reader.auto_import_models(project_root, parent_dir, args.pattern)
    
    # [제어 흐름 및 비즈니스 분기] CLI 인자로 명시적인 Base 모듈 경로가 전달되었는지 여부에 따라 동적 스캔 모드와 고정 임포트 모드 분기
    if args.base:
        try:
            module_name, var_name = args.base.split(":")
            module = importlib.import_module(module_name)
            base_obj = getattr(module, var_name, None)
        except Exception as e:
            logger.error(f"Failed to import specified Base '{args.base}': {e}")
    else:
        logger.info("Base not specified. Scanning project to discover declarative base dynamically...")
        base_obj = reader.discover_base_class(project_root, parent_dir)
        
    metadata = reader.get_metadata(base_obj) if base_obj is not None else None
    has_rdb = (metadata is not None and len(metadata.tables) > 0)
    
    # [데이터 I/O] reader를 통해 파이어스토어 컬렉션 메타데이터 수집
    firestore_collections = reader.read_firestore_metadata(project_root)
    has_firestore = len(firestore_collections) > 0
    
    # [제어 흐름 및 비즈니스 분기] RDB와 Firestore 둘 다 감지되지 않는 경우 출력 대상이 없으므로 중단합니다.
    if not has_rdb and not has_firestore:
        logger.error("Neither SQLAlchemy RDB models nor Firestore collections were detected. Execution aborted.")
        sys.exit(1)
        
    GENERATORS: dict[str, Callable[[Any, str], bool]] = {
        ".sql": generate_sql_ddl,
        ".md": lambda meta, out: generate_firestore_erd(project_root, out)
    }

    # [제어 흐름 및 비즈니스 분기] 실행 인자가 없거나 명시적으로 'all'이 입력된 경우 지원되는 전체 형식 일괄 생성 로직을 분기 실행
    if args.output.lower() == "all":
        logger.info("Running in 'all' mode. Generating SQL, PNG, and Firestore Markdown formats inside erd/ directory...")
        
        sql_path = _resolve_output_path("erd.sql", script_dir)
        png_path = _resolve_output_path("erd.png", script_dir)
        firestore_path = _resolve_output_path("firestore_erd.md", script_dir)
        
        success = True
        
        # [제어 흐름 및 비즈니스 분기] RDB 테이블이 존재하는 경우에 한하여 SQL DDL 및 PNG 다이어그램 생성
        if has_rdb:
            if not generate_sql_ddl(metadata, sql_path):
                success = False
            if not generate_png_erd(base_obj, png_path):
                success = False
        else:
            logger.info("No SQLAlchemy RDB models detected. Skipping RDB generation.")
            
        # [제어 흐름 및 비즈니스 분기] 파이어스토어 컬렉션이 존재하는 경우에 한하여 Mermaid 마크다운 생성
        if has_firestore:
            if not generate_firestore_erd(project_root, firestore_path):
                success = False
        else:
            logger.info("No Firestore collections detected. Skipping Firestore generation.")
            
        sys.exit(0 if success else 1)
    
    # 단일 포맷 생성 및 연계 생성 (.sql 지정 시 편의상 .png도 병행 생성 시도)
    output_file: str = _resolve_output_path(args.output, script_dir)
    file_extension: str = os.path.splitext(output_file)[1].lower()
    
    # [제어 흐름 및 비즈니스 분기] PNG 형식과 다른 텍스트 형식의 인자 수용 및 라우팅 분기
    if file_extension == ".png":
        # [제어 흐름 및 비즈니스 분기] PNG 생성을 요청했으나 RDB 테이블이 없는 경우 오류로 처리
        if not has_rdb:
            logger.error("Requested PNG output, but no SQLAlchemy RDB models were detected.")
            sys.exit(1)
        is_successful = generate_png_erd(base_obj, output_file)
    else:
        diagram_generator: Optional[Callable[[Any, str], bool]] = GENERATORS.get(file_extension)
        # [제어 흐름 및 비즈니스 분기] 지원하지 않는 확장자의 다이어그램 생성을 요청한 경우 실행을 거부하기 위한 방어적 에러 분기
        if not diagram_generator:
            logger.error(f"Unsupported extension: {file_extension}")
            sys.exit(1)
            
        # [제어 흐름 및 비즈니스 분기] 특정 확장에 따른 RDB/Firestore 데이터 존재 여부 유효성 검증
        if file_extension == ".sql" and not has_rdb:
            logger.error("Requested SQL DDL output, but no SQLAlchemy RDB models were detected.")
            sys.exit(1)
        if file_extension == ".md" and not has_firestore:
            logger.error("Requested Markdown output, but no Firestore collections were detected.")
            sys.exit(1)
            
        is_successful = diagram_generator(metadata, output_file)
        
        # [제어 흐름 및 비즈니스 분기] .sql 확장자 빌드가 성공한 경우, 유저의 시각적 편의를 위해 연동하여 .png 이미지 파일 생성을 추가 병행하도록 제어 분기
        if is_successful and file_extension == ".sql":
            png_file_path: str = output_file.replace(".sql", ".png")
            generate_png_erd(base_obj, png_file_path)
        
    sys.exit(0 if is_successful else 1)

if __name__ == "__main__":
    main()
