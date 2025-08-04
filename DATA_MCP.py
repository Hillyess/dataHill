#!/usr/bin/env python3
"""
IPython 数据分析 MCP 服务器
基于真正 IPython 内核的轻量级数据分析 MCP 工具
提供完整的交互式 Python 数据分析环境，支持会话管理、数据加载、实时数据查看等核心功能

完整使用示例:
```python
# 1. 创建会话
result = create_ipython_session()
session_id = result["session_id"]

# 2. 加载数据
load_csv_file("data.csv", session_id, "df")
# 或加载Excel文件 (支持.xlsx和.xls)
load_excel_file("data.xlsx", session_id, "df_excel")

# 3. 查看数据信息
get_dataframe_info("df", session_id)

# 4. 智能采样查看列数据 (避免大数据集上下文填满)
sample_column_data("df", "column_name", session_id, method="mixed", sample_size=20)

# 5. 执行分析
execute_code("df.describe()", session_id)

# 6. 数据可视化
execute_code("df.plot()", session_id)

# 7. 内存检查
check_memory_usage(session_id)

# 8. 清理会话
delete_ipython_session(session_id)
```

支持的功能:
- 17个核心函数，涵盖会话管理、代码执行、数据加载、内存监控
- 真正的 IPython 环境，支持魔法命令和系统命令行命令
- 自动编码检测，支持中文CSV文件
- 完整的Excel支持，同时支持.xlsx和.xls格式
- 智能列数据采样查看，避免大数据集上下文填满
- 完整的数据分析工具集成
- 实时内存监控和变量管理
"""

import os
import sys
import threading
import time
import uuid
import traceback
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# System monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# IPython imports
try:
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False
    print("警告: IPython 未安装，请执行: pip install ipython")

# Data processing imports
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("警告: pandas/numpy 未安装，请执行: pip install pandas numpy")

# Excel support
try:
    import openpyxl
    EXCEL_XLSX_AVAILABLE = True
except ImportError:
    EXCEL_XLSX_AVAILABLE = False

try:
    import xlrd
    EXCEL_XLS_AVAILABLE = True
except ImportError:
    EXCEL_XLS_AVAILABLE = False

EXCEL_AVAILABLE = EXCEL_XLSX_AVAILABLE or EXCEL_XLS_AVAILABLE

# MCP imports
from fastmcp import FastMCP
from pydantic import BaseModel

# 创建MCP应用实例
mcp = FastMCP("IPython Data Analysis MCP Server")

# 全局会话管理器
_session_manager = None
_session_lock = threading.Lock()

class ExecutionResult(BaseModel):
    """代码执行结果模型"""
    success: bool
    execution_count: int
    stdout: str
    stderr: str
    result: Optional[str] = None
    execution_time: float
    memory_delta_mb: float
    error: Optional[str] = None

class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str
    status: str
    created_at: str
    last_used: str
    execution_count: int
    memory_usage_mb: float
    variable_count: int

def remove_ansi_codes(text: str) -> str:
    """移除文本中的 ANSI 转义序列"""
    if not text:
        return text
    # ANSI 转义序列的正则表达式
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class IPythonSession:
    """IPython 会话封装"""
    
    def __init__(self, session_id: str, auto_import: bool = True):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.execution_count = 0
        self.history = []
        
        if not IPYTHON_AVAILABLE:
            raise ImportError("IPython is required but not available")
        
        # 创建独立的 IPython shell 实例
        self.shell = InteractiveShell()
        
        # 配置无颜色模式以避免 ANSI 代码
        self.shell.colors = 'NoColor'
        
        # 配置 PlainTextFormatter 减少详细输出
        try:
            plain_formatter = self.shell.display_formatter.formatters['text/plain']
            plain_formatter.verbose = False
        except:
            pass
        
        # 禁用 GUI
        self.shell.enable_gui = lambda x: None
        
        # 设置 matplotlib 后端为 Agg (non-interactive)
        try:
            self.shell.run_cell("import matplotlib; matplotlib.use('Agg')")
        except:
            pass
        
        if auto_import:
            self._auto_import_libraries()
    
    def _auto_import_libraries(self) -> List[str]:
        """自动导入常用库"""
        imported = []
        import_code = """
            import pandas as pd
            import numpy as np
            import json
            import os
            import sys
            from pathlib import Path
            import warnings
            warnings.filterwarnings('ignore')

            # 设置pandas显示选项
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', 100)

            print("✓ 已自动导入: pandas, numpy, json, os, sys, pathlib")
            """
        
        try:
            result = self.shell.run_cell(import_code)
            if not result.error_in_exec:
                imported = ["pandas", "numpy", "json", "os", "sys", "pathlib"]
        except Exception as e:
            print(f"自动导入失败: {e}")
        
        return imported
    
    def _format_result(self, result_obj: Any) -> str:
        """使用 IPython DisplayFormatter 格式化结果对象"""
        if result_obj is None:
            return None
        
        try:
            # 优先使用 IPython 的 DisplayFormatter 系统
            format_dict, _ = self.shell.display_formatter.format(
                result_obj, 
                include=['text/plain']
            )
            formatted_result = format_dict.get('text/plain')
            
            if formatted_result:
                return formatted_result
                
        except Exception:
            # 如果 DisplayFormatter 失败，回退到传统方法
            pass
        
        # 回退方案：传统格式化方法
        try:
            # 对于 DataFrame，使用 to_string() 方法获得更好的格式
            if hasattr(result_obj, 'to_string'):
                return result_obj.to_string()
            
            # 对于 numpy 数组，使用 __str__ 方法
            if hasattr(result_obj, '__array__'):
                return str(result_obj)
            
            # 对于其他对象，使用 str()
            return str(result_obj)
            
        except Exception:
            return str(result_obj)
    
    def _format_result_direct(self, result_obj: Any) -> str:
        """直接使用 PlainTextFormatter 格式化结果"""
        if result_obj is None:
            return None
        
        try:
            # 直接使用 PlainTextFormatter
            plain_formatter = self.shell.display_formatter.formatters['text/plain']
            formatted_result = plain_formatter(result_obj)
            
            if formatted_result:
                return formatted_result
                
        except Exception:
            # 如果直接格式化失败，使用回退方案
            pass
        
        # 回退到传统格式化方法
        return self._format_result(result_obj)
    
    def execute_expression_only(self, code: str) -> ExecutionResult:
        """只执行表达式并返回结果，不捕获 print 输出 - 适用于纯表达式求值"""
        self.last_used = datetime.now()
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        try:
            # 确保使用无颜色模式
            original_colors = getattr(self.shell, 'colors', 'NoColor')
            self.shell.colors = 'NoColor'
            
            # 直接执行，不捕获输出
            execution_result = self.shell.run_cell(code, store_history=True)
            
            # 恢复颜色设置
            self.shell.colors = original_colors
            
            self.execution_count += 1
            execution_time = time.time() - start_time
            current_memory = self._get_memory_usage()
            memory_delta = current_memory - initial_memory
            
            # 直接使用 PlainTextFormatter 格式化结果
            formatted_result = self._format_result_direct(execution_result.result)
            
            # 处理错误信息
            error_msg = None
            if execution_result.error_in_exec:
                error_msg = remove_ansi_codes(str(execution_result.error_in_exec))
            
            # 记录执行历史
            history_entry = {
                'execution_count': self.execution_count,
                'timestamp': self.last_used.isoformat(),
                'code': code,
                'success': not bool(execution_result.error_in_exec),
                'execution_time': execution_time,
                'stdout': "",  # 不捕获 stdout
                'stderr': "",  # 不捕获 stderr
                'result': formatted_result,
                'error': error_msg
            }
            self.history.append(history_entry)
            
            # 保持历史记录在合理大小
            if len(self.history) > 100:
                self.history = self.history[-100:]
            
            return ExecutionResult(
                success=not bool(execution_result.error_in_exec),
                execution_count=self.execution_count,
                stdout="",  # 不返回 stdout
                stderr="",  # 不返回 stderr
                result=formatted_result,
                execution_time=execution_time,
                memory_delta_mb=memory_delta,
                error=error_msg
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"执行错误: {str(e)}\n{traceback.format_exc()}"
            
            return ExecutionResult(
                success=False,
                execution_count=self.execution_count,
                stdout="",
                stderr="",
                result=None,
                execution_time=execution_time,
                memory_delta_mb=0.0,
                error=remove_ansi_codes(error_msg)
            )
    
    def execute(self, code: str) -> ExecutionResult:
        """执行代码并返回结果 - 使用混合输出处理方案"""
        self.last_used = datetime.now()
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        try:
            # 确保使用无颜色模式
            original_colors = getattr(self.shell, 'colors', 'NoColor')
            self.shell.colors = 'NoColor'
            
            # 使用 IPython 的 capture_output 捕获 print 输出和 stderr
            with capture_output() as captured:
                execution_result = self.shell.run_cell(code, store_history=True)
            
            # 恢复颜色设置
            self.shell.colors = original_colors
            
            self.execution_count += 1
            execution_time = time.time() - start_time
            current_memory = self._get_memory_usage()
            memory_delta = current_memory - initial_memory
            
            # 清理输出中可能残留的 ANSI 代码
            stdout = remove_ansi_codes(captured.stdout)
            stderr = remove_ansi_codes(captured.stderr)
            
            # 使用 DisplayFormatter 格式化表达式结果
            formatted_result = self._format_result(execution_result.result)
            
            # 处理错误信息
            error_msg = None
            if execution_result.error_in_exec:
                error_msg = remove_ansi_codes(str(execution_result.error_in_exec))
            
            # 记录执行历史
            history_entry = {
                'execution_count': self.execution_count,
                'timestamp': self.last_used.isoformat(),
                'code': code,
                'success': not bool(execution_result.error_in_exec),
                'execution_time': execution_time,
                'stdout': stdout,
                'stderr': stderr,
                'result': formatted_result,
                'error': error_msg
            }
            self.history.append(history_entry)
            
            # 保持历史记录在合理大小
            if len(self.history) > 100:
                self.history = self.history[-100:]
            
            return ExecutionResult(
                success=not bool(execution_result.error_in_exec),
                execution_count=self.execution_count,
                stdout=stdout,
                stderr=stderr,
                result=formatted_result,
                execution_time=execution_time,
                memory_delta_mb=memory_delta,
                error=error_msg
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"执行错误: {str(e)}\n{traceback.format_exc()}"
            
            return ExecutionResult(
                success=False,
                execution_count=self.execution_count,
                stdout="",
                stderr="",
                result=None,
                execution_time=execution_time,
                memory_delta_mb=0.0,
                error=remove_ansi_codes(error_msg)
            )
    
    def get_variables(self) -> Dict[str, Any]:
        """获取当前命名空间中的变量"""
        variables = {}
        user_ns = self.shell.user_ns
        
        for name, value in user_ns.items():
            if not name.startswith('_') and name not in ['In', 'Out', 'get_ipython', 'exit', 'quit']:
                try:
                    var_type = type(value).__name__
                    var_info = {
                        'type': var_type,
                        'size_bytes': sys.getsizeof(value)
                    }
                    
                    # 特殊处理不同类型的变量
                    if hasattr(value, 'shape') and hasattr(value, 'dtypes'):  # DataFrame
                        var_info.update({
                            'shape': list(value.shape),
                            'columns': list(value.columns) if hasattr(value, 'columns') else None,
                            'memory_usage': value.memory_usage(deep=True).sum() if hasattr(value, 'memory_usage') else None
                        })
                    elif hasattr(value, 'shape'):  # numpy array
                        var_info.update({
                            'shape': list(value.shape),
                            'dtype': str(value.dtype) if hasattr(value, 'dtype') else None
                        })
                    elif isinstance(value, (list, tuple, dict, set)):
                        var_info['length'] = len(value)
                    
                    variables[name] = var_info
                    
                except Exception:
                    variables[name] = {'type': var_type, 'size_bytes': 0}
        
        return variables
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量(MB)"""
        if not PSUTIL_AVAILABLE:
            return 0.0
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def get_memory_info(self) -> Dict[str, Any]:
        """获取详细内存信息"""
        variables = self.get_variables()
        
        # 按类型分组统计内存使用
        breakdown = {
            'dataframes': 0.0,
            'lists': 0.0,
            'scalars': 0.0,
            'functions': 0.0,
            'others': 0.0
        }
        
        top_variables = []
        
        for name, var_info in variables.items():
            memory_mb = var_info.get('size_bytes', 0) / 1024 / 1024
            var_type = var_info.get('type', 'unknown')
            
            # 特殊处理 DataFrame 内存使用
            if 'memory_usage' in var_info and var_info['memory_usage']:
                memory_mb = var_info['memory_usage'] / 1024 / 1024
            
            top_variables.append({
                'name': name,
                'type': var_type,
                'memory_mb': round(memory_mb, 2)
            })
            
            # 分类统计
            if 'DataFrame' in var_type:
                breakdown['dataframes'] += memory_mb
            elif var_type in ['list', 'tuple', 'set']:
                breakdown['lists'] += memory_mb
            elif var_type in ['int', 'float', 'str', 'bool']:
                breakdown['scalars'] += memory_mb
            elif 'function' in var_type.lower():
                breakdown['functions'] += memory_mb
            else:
                breakdown['others'] += memory_mb
        
        # 按内存使用排序
        top_variables.sort(key=lambda x: x['memory_mb'], reverse=True)
        
        # 系统内存信息
        if PSUTIL_AVAILABLE:
            try:
                system_memory = psutil.virtual_memory()
                system_info = {
                    'available_mb': round(system_memory.available / 1024 / 1024, 1),
                    'used_percent': system_memory.percent
                }
            except:
                system_info = {'available_mb': 0, 'used_percent': 0}
        else:
            system_info = {'available_mb': 0, 'used_percent': 0}
        
        total_memory = sum(breakdown.values())
        
        return {
            'total_memory_mb': round(total_memory, 1),
            'breakdown': {k: round(v, 1) for k, v in breakdown.items()},
            'top_variables': top_variables[:10],  # 前10个最大的变量
            'system_memory': system_info
        }

class IPythonSessionManager:
    """IPython 会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, IPythonSession] = {}
        self.lock = threading.Lock()
    
    def create_session(self, session_id: Optional[str] = None, auto_import: bool = True) -> str:
        """创建新会话"""
        with self.lock:
            if session_id is None:
                session_id = f"session_{uuid.uuid4().hex[:8]}"
            
            if session_id in self.sessions:
                raise ValueError(f"Session {session_id} already exists")
            
            session = IPythonSession(session_id, auto_import)
            self.sessions[session_id] = session
            return session_id
    
    def get_session(self, session_id: str) -> IPythonSession:
        """获取会话"""
        with self.lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            return self.sessions[session_id]
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
    
    def list_sessions(self) -> List[SessionInfo]:
        """列出所有会话"""
        with self.lock:
            sessions = []
            for session_id, session in self.sessions.items():
                variables = session.get_variables()
                memory_info = session.get_memory_info()
                
                sessions.append(SessionInfo(
                    session_id=session_id,
                    status="active",
                    created_at=session.created_at.isoformat(),
                    last_used=session.last_used.isoformat(),
                    execution_count=session.execution_count,
                    memory_usage_mb=memory_info['total_memory_mb'],
                    variable_count=len(variables)
                ))
            return sessions

class DataLoader:
    """数据加载器"""
    
    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """自动检测文件编码"""
        encodings = ['utf-8', 'gb18030', 'gbk', 'gb2312', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 读取一部分内容进行测试
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        return 'utf-8'  # 默认编码
    
    @staticmethod
    def load_csv(file_path: str, encoding: str = "auto") -> tuple:
        """加载 CSV 文件"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for CSV loading")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if encoding == "auto":
            encoding = DataLoader.detect_encoding(file_path)
        
        start_time = time.time()
        df = pd.read_csv(file_path, encoding=encoding)
        load_time = time.time() - start_time
        
        return df, encoding, load_time
    
    @staticmethod
    def load_excel(file_path: str, sheet_name: Union[str, int] = 0):
        """加载 Excel 文件 - 支持 .xlsx 和 .xls 格式"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for Excel loading")
        
        if not EXCEL_AVAILABLE:
            raise ImportError("Excel support libraries are required. Install with: pip install openpyxl xlrd")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 检测文件扩展名并选择合适的引擎
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.xlsx':
            if not EXCEL_XLSX_AVAILABLE:
                raise ImportError("openpyxl is required for .xlsx files. Install with: pip install openpyxl")
            engine = 'openpyxl'
        elif file_extension == '.xls':
            if not EXCEL_XLS_AVAILABLE:
                raise ImportError("xlrd is required for .xls files. Install with: pip install xlrd")
            engine = 'xlrd'
        else:
            # 默认尝试使用openpyxl，如果失败则尝试xlrd
            engine = None
        
        start_time = time.time()
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine)
        except Exception as e:
            if engine is None and file_extension not in ['.xlsx', '.xls']:
                # 尝试不同的引擎
                for alt_engine in ['openpyxl', 'xlrd']:
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=alt_engine)
                        break
                    except:
                        continue
                else:
                    raise e
            else:
                raise e
        
        load_time = time.time() - start_time
        
        return df, load_time
    
    @staticmethod
    def load_json(file_path: str):
        """加载 JSON 文件"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for JSON loading")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        start_time = time.time()
        df = pd.read_json(file_path)
        load_time = time.time() - start_time
        
        return df, load_time

def get_session_manager() -> IPythonSessionManager:
    """获取全局会话管理器"""
    global _session_manager
    if _session_manager is None:
        _session_manager = IPythonSessionManager()
    return _session_manager

# =============================================================================
# MCP 工具函数实现
# =============================================================================

@mcp.tool()
def create_ipython_session(
    session_id: Optional[str] = None,
    auto_import: bool = True
) -> Dict[str, Any]:
    """
    创建新的 IPython 会话
    
    功能说明:
    - 创建一个独立的 IPython 交互式会话环境
    - 每个会话拥有独立的命名空间，变量不会相互影响
    - 可选择自动导入常用数据科学库 (pandas, numpy, matplotlib等)
    - 支持所有 IPython 功能：Python代码、魔法命令、系统命令
    
    Args:
        session_id: 会话ID，可选，不提供则自动生成 (格式: session_xxxxxxxx)
        auto_import: 是否自动导入常用库 (pandas, numpy, json, os, sys, pathlib)
    
    Returns:
        Dict: 包含会话创建结果的字典
    
    调用样例:
    ```python
    # 创建会话，自动生成ID
    result = create_ipython_session()
    
    # 创建指定ID的会话，不自动导入库
    result = create_ipython_session(session_id="my_session", auto_import=False)
    ```
    
    返回格式:
    成功时包含: success, session_id, message, auto_imported (导入的库列表)
    失败时包含: success, error
    """
    try:
        if not IPYTHON_AVAILABLE:
            return {
                "success": False,
                "error": "IPython is not available. Please install with: pip install ipython"
            }
        
        manager = get_session_manager()
        created_session_id = manager.create_session(session_id, auto_import)
        
        auto_imported = []
        if auto_import:
            auto_imported = ["pandas", "numpy", "json", "os", "sys", "pathlib"]
        
        return {
            "success": True,
            "session_id": created_session_id,
            "message": f"IPython session {created_session_id} created successfully",
            "auto_imported": auto_imported
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create session: {str(e)}"
        }

@mcp.tool()
def list_ipython_sessions() -> Dict[str, Any]:
    """
    列出所有活跃的 IPython 会话
    
    功能说明:
    - 获取当前所有活跃会话的基本信息
    - 显示每个会话的创建时间、最后使用时间、执行次数等
    - 显示会话的内存使用情况和变量数量
    - 用于会话管理和监控
    
    Args:
        无参数
    
    Returns:
        Dict: 包含所有会话信息的字典
    
    调用样例:
    ```python
    # 列出所有会话
    result = list_ipython_sessions()
    ```
    
    返回格式:
    成功时包含: success, sessions (会话列表), total_sessions
    每个会话包含: session_id, status, created_at, last_used, execution_count, memory_usage_mb, variable_count
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        sessions = manager.list_sessions()
        
        return {
            "success": True,
            "sessions": [session.model_dump() for session in sessions],
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list sessions: {str(e)}"
        }

@mcp.tool()
def get_session_status(session_id: str) -> Dict[str, Any]:
    """
    获取指定会话的详细状态信息
    
    功能说明:
    - 获取会话的详细状态信息
    - 包含内存使用详情和变量统计
    - 按变量类型分组统计
    
    Args:
        session_id: 会话ID
    
    调用样例:
    ```python
    result = get_session_status(session_id="session_a1b2c3d4")
    ```
    
    返回格式:
    成功时包含: success, session_info (状态、时间、内存使用、变量统计)
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        variables = session.get_variables()
        memory_info = session.get_memory_info()
        
        # 按类型统计变量
        variable_summary = {
            'dataframes': 0,
            'lists': 0,
            'scalars': 0,
            'functions': 0,
            'others': 0
        }
        
        for var_info in variables.values():
            var_type = var_info.get('type', 'unknown')
            if 'DataFrame' in var_type:
                variable_summary['dataframes'] += 1
            elif var_type in ['list', 'tuple', 'set']:
                variable_summary['lists'] += 1
            elif var_type in ['int', 'float', 'str', 'bool']:
                variable_summary['scalars'] += 1
            elif 'function' in var_type.lower():
                variable_summary['functions'] += 1
            else:
                variable_summary['others'] += 1
        
        return {
            "success": True,
            "session_info": {
                "session_id": session_id,
                "status": "active",
                "created_at": session.created_at.isoformat(),
                "last_used": session.last_used.isoformat(),
                "execution_count": session.execution_count,
                "memory_usage": {
                    "total_mb": memory_info['total_memory_mb'],
                    "breakdown": memory_info['breakdown']
                },
                "variable_summary": variable_summary
            }
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get session status: {str(e)}"
        }

@mcp.tool()
def delete_ipython_session(session_id: str) -> Dict[str, Any]:
    """
    删除指定的 IPython 会话
    
    功能说明:
    - 删除指定的会话及其所有数据
    - 释放会话占用的内存
    
    Args:
        session_id: 会话ID
    
    调用样例:
    ```python
    result = delete_ipython_session(session_id="session_a1b2c3d4")
    ```
    
    返回格式:
    成功时包含: success, message
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        success = manager.delete_session(session_id)
        
        if success:
            return {
                "success": True,
                "message": f"Session {session_id} deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to delete session: {str(e)}"
        }

@mcp.tool()
def execute_code(
    code: str,
    session_id: str,
    capture_output: bool = True,
    expression_only: bool = False
) -> Dict[str, Any]:
    """
    在指定会话中执行代码
    
    功能说明:
    - 在指定的 IPython 会话中执行代码
    - 支持三种代码类型：Python代码、IPython魔法命令、系统命令
    - 自动捕获执行输出、错误信息和返回值
    - 记录执行时间和内存变化
    - 所有变量状态在会话中持久保存
    - 支持两种执行模式：完整模式和表达式模式
    
    支持的代码类型:
    - Python代码: x = 1 + 1、import pandas as pd、df.head()
    - 魔法命令: %timeit sum(range(100))、%matplotlib inline、%who、%whos
    - 命令行命令: !ls -la、!pip install numpy、!pwd、!cat file.txt
    
    Args:
        code: 要执行的代码（支持多行）
        session_id: 会话ID
        capture_output: 是否捕获输出（保留参数，目前总是捕获）
        expression_only: 是否使用表达式模式（True时只返回表达式结果，不捕获print输出）
    
    Returns:
        Dict: 执行结果
    
    调用样例:
    ```python
    # Python代码执行（完整模式，捕获print输出）
    result = execute_code(
        code="x = 10\ny = 20\nprint(f'x + y = {x + y}')",
        session_id="session_a1b2c3d4"
    )
    
    # 表达式模式（只返回表达式结果，不捕获print输出）
    result = execute_code(
        code="df.head()",
        session_id="session_a1b2c3d4",
        expression_only=True
    )
    
    # 魔法命令执行
    result = execute_code(
        code="%timeit sum(range(1000))",
        session_id="session_a1b2c3d4"
    )
    
    # 系统命令执行
    result = execute_code(
        code="!ls -la",
        session_id="session_a1b2c3d4"
    )
    
    # 多行代码执行
    result = execute_code(
        code=\"\"\"
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
print("DataFrame created:")
df.head()
\"\"\",
        session_id="session_a1b2c3d4"
    )
    ```
    
    返回格式:
    包含: success, execution_count, stdout, stderr, result, execution_time, memory_delta_mb, error
    成功时 error 为 null，失败时 error 包含错误信息
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        # 根据参数选择执行方法
        if expression_only:
            result = session.execute_expression_only(code)
        else:
            result = session.execute(code)
        
        return {
            "success": result.success,
            "execution_count": result.execution_count,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "result": result.result,
            "execution_time": round(result.execution_time, 3),
            "memory_delta_mb": round(result.memory_delta_mb, 2),
            "error": result.error
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to execute code: {str(e)}"
        }

@mcp.tool()
def get_execution_history(
    session_id: str,
    limit: int = 10,
    include_output: bool = False
) -> Dict[str, Any]:
    """
    获取会话的执行历史
    
    功能说明:
    - 获取会话中的代码执行历史记录
    - 可选择包含或排除执行输出
    - 支持限制返回数量
    
    Args:
        session_id: 会话ID
        limit: 返回的历史记录数量
        include_output: 是否包含输出结果
    
    调用样例:
    ```python
    # 获取最近10条历史，不包含输出
    result = get_execution_history(session_id="session_a1b2c3d4", limit=10)
    
    # 获取最近5条历史，包含输出
    result = get_execution_history(session_id="session_a1b2c3d4", limit=5, include_output=True)
    ```
    
    返回格式:
    成功时包含: success, history (历史记录列表), total_executions
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        history = session.history[-limit:] if limit > 0 else session.history
        
        if not include_output:
            # 移除输出内容以节省空间
            history = [
                {k: v for k, v in entry.items() 
                 if k not in ['stdout', 'stderr', 'result']}
                for entry in history
            ]
        
        return {
            "success": True,
            "history": history,
            "total_executions": len(session.history)
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get execution history: {str(e)}"
        }

@mcp.tool()
def load_csv_file(
    file_path: str,
    session_id: str,
    variable_name: Optional[str] = None,
    encoding: str = "auto"
) -> Dict[str, Any]:
    """
    加载 CSV 文件到 DataFrame
    
    功能说明:
    - 将 CSV 文件加载为 pandas DataFrame 并存储到指定会话中
    - 自动检测文件编码，支持中文文件
    - 自动生成变量名或使用指定变量名
    - 返回 DataFrame 的详细信息（形状、列名、数据类型、内存使用等）
    - 支持各种 CSV 格式和分隔符
    
    Args:
        file_path: CSV文件的绝对或相对路径
        session_id: 目标会话ID
        variable_name: 存储的变量名，不提供则自动生成 (格式: df_文件名)
        encoding: 文件编码，"auto"为自动检测，支持 utf-8, gbk, gb2312 等
    
    Returns:
        Dict: 加载结果，包含 DataFrame 信息
    
    调用样例:
    ```python
    # 基本加载，自动生成变量名
    result = load_csv_file(
        file_path="/path/to/sales_data.csv",
        session_id="session_a1b2c3d4"
    )
    
    # 指定变量名和编码
    result = load_csv_file(
        file_path="./data/中文数据.csv",
        session_id="session_a1b2c3d4",
        variable_name="chinese_data",
        encoding="gb2312"
    )
    
    # 自动编码检测
    result = load_csv_file(
        file_path="data.csv",
        session_id="session_a1b2c3d4",
        encoding="auto"  # 默认值
    )
    ```
    
    返回格式:
    成功时包含: success, variable_name, shape, columns, dtypes, memory_usage_mb, encoding_detected, load_time
    失败时包含: success, error
    """
    try:
        if not PANDAS_AVAILABLE:
            return {
                "success": False,
                "error": "pandas is not available. Please install with: pip install pandas numpy"
            }
        
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        # 加载数据
        df, detected_encoding, load_time = DataLoader.load_csv(file_path, encoding)
        
        # 生成变量名
        if variable_name is None:
            base_name = Path(file_path).stem
            variable_name = f"df_{base_name}"
            
            # 确保变量名不冲突
            variables = session.get_variables()
            counter = 1
            while variable_name in variables:
                variable_name = f"df_{base_name}_{counter}"
                counter += 1
        
        # 将DataFrame添加到会话命名空间
        session.shell.user_ns[variable_name] = df
        
        # 获取DataFrame信息
        dtypes_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}
        memory_usage_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        return {
            "success": True,
            "variable_name": variable_name,
            "shape": list(df.shape),
            "columns": list(df.columns),
            "dtypes": dtypes_dict,
            "memory_usage_mb": round(memory_usage_mb, 2),
            "encoding_detected": detected_encoding,
            "load_time": round(load_time, 3)
        }
        
    except FileNotFoundError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load CSV file: {str(e)}"
        }

@mcp.tool()
def load_excel_file(
    file_path: str,
    session_id: str,
    variable_name: Optional[str] = None,
    sheet_name: Union[str, int] = 0
) -> Dict[str, Any]:
    """
    加载 Excel 文件到 DataFrame
    
    功能说明:
    - 加载 Excel 文件到 pandas DataFrame
    - 支持多个工作表选择
    - 自动生成变量名
    
    Args:
        file_path: Excel文件路径
        session_id: 会话ID
        variable_name: 变量名，不提供则自动生成
        sheet_name: 工作表名称或索引 (默认0)
    
    调用样例:
    ```python
    # 加载默认工作表
    result = load_excel_file("data.xlsx", "session_a1b2c3d4")
    
    # 加载指定工作表
    result = load_excel_file("data.xlsx", "session_a1b2c3d4", sheet_name="Sheet2")
    ```
    
    返回格式:
    成功时包含: success, variable_name, shape, columns, dtypes, memory_usage_mb, sheet_name, load_time
    失败时包含: success, error
    """
    try:
        if not PANDAS_AVAILABLE:
            return {
                "success": False,
                "error": "pandas is not available. Please install with: pip install pandas numpy"
            }
        
        if not EXCEL_AVAILABLE:
            return {
                "success": False,
                "error": "Excel support libraries are not available. Please install with: pip install openpyxl xlrd"
            }
        
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        # 加载数据
        df, load_time = DataLoader.load_excel(file_path, sheet_name)
        
        # 生成变量名
        if variable_name is None:
            base_name = Path(file_path).stem
            variable_name = f"df_{base_name}"
            
            # 确保变量名不冲突
            variables = session.get_variables()
            counter = 1
            while variable_name in variables:
                variable_name = f"df_{base_name}_{counter}"
                counter += 1
        
        # 将DataFrame添加到会话命名空间
        session.shell.user_ns[variable_name] = df
        
        # 获取DataFrame信息
        dtypes_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}
        memory_usage_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        return {
            "success": True,
            "variable_name": variable_name,
            "shape": list(df.shape),
            "columns": list(df.columns),
            "dtypes": dtypes_dict,
            "memory_usage_mb": round(memory_usage_mb, 2),
            "sheet_name": sheet_name,
            "load_time": round(load_time, 3)
        }
        
    except FileNotFoundError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load Excel file: {str(e)}"
        }

@mcp.tool()
def load_json_file(
    file_path: str,
    session_id: str,
    variable_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    加载 JSON 文件到 DataFrame
    
    功能说明:
    - 加载 JSON 文件到 pandas DataFrame
    - 自动推断JSON结构
    - 支持嵌套JSON数据
    
    Args:
        file_path: JSON文件路径
        session_id: 会话ID
        variable_name: 变量名，不提供则自动生成
    
    调用样例:
    ```python
    result = load_json_file("data.json", "session_a1b2c3d4")
    ```
    
    返回格式:
    成功时包含: success, variable_name, shape, columns, dtypes, memory_usage_mb, load_time
    失败时包含: success, error
    """
    try:
        if not PANDAS_AVAILABLE:
            return {
                "success": False,
                "error": "pandas is not available. Please install with: pip install pandas numpy"
            }
        
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        # 加载数据
        df, load_time = DataLoader.load_json(file_path)
        
        # 生成变量名
        if variable_name is None:
            base_name = Path(file_path).stem
            variable_name = f"df_{base_name}"
            
            # 确保变量名不冲突
            variables = session.get_variables()
            counter = 1
            while variable_name in variables:
                variable_name = f"df_{base_name}_{counter}"
                counter += 1
        
        # 将DataFrame添加到会话命名空间
        session.shell.user_ns[variable_name] = df
        
        # 获取DataFrame信息
        dtypes_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}
        memory_usage_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        return {
            "success": True,
            "variable_name": variable_name,
            "shape": list(df.shape),
            "columns": list(df.columns),
            "dtypes": dtypes_dict,
            "memory_usage_mb": round(memory_usage_mb, 2),
            "load_time": round(load_time, 3)
        }
        
    except FileNotFoundError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load JSON file: {str(e)}"
        }

@mcp.tool()
def list_dataframes(session_id: str) -> Dict[str, Any]:
    """
    列出会话中所有 DataFrame 变量
    
    功能说明:
    - 列出会话中所有DataFrame变量
    - 显示每个DataFrame的基本信息
    - 统计总内存使用
    
    Args:
        session_id: 会话ID
    
    调用样例:
    ```python
    result = list_dataframes(session_id="session_a1b2c3d4")
    ```
    
    返回格式:
    成功时包含: success, dataframes (列表), total_dataframes, total_memory_mb
    每个DataFrame包含: name, shape, memory_mb, columns
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        variables = session.get_variables()
        dataframes = []
        total_memory = 0.0
        
        for name, var_info in variables.items():
            if 'DataFrame' in var_info.get('type', ''):
                # 获取DataFrame对象
                df = session.shell.user_ns.get(name)
                if df is not None and hasattr(df, 'shape'):
                    memory_mb = var_info.get('memory_usage', 0) / 1024 / 1024 if var_info.get('memory_usage') else 0
                    total_memory += memory_mb
                    
                    dataframes.append({
                        "name": name,
                        "shape": list(df.shape),
                        "memory_mb": round(memory_mb, 2),
                        "columns": list(df.columns)[:10]  # 只显示前10列
                    })
        
        return {
            "success": True,
            "dataframes": dataframes,
            "total_dataframes": len(dataframes),
            "total_memory_mb": round(total_memory, 2)
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list dataframes: {str(e)}"
        }

@mcp.tool()
def get_dataframe_info(
    variable_name: str,
    session_id: str
) -> Dict[str, Any]:
    """
    获取指定 DataFrame 的详细信息
    
    功能说明:
    - 获取 DataFrame 的完整元数据信息
    - 包括形状、列名、数据类型、内存使用、缺失值统计等
    - 提供每列的详细内存使用情况
    - 显示索引信息和数据完整性状态
    - 用于数据质量检查和内存优化
    
    Args:
        variable_name: 会话中 DataFrame 变量的名称
        session_id: 会话ID
    
    Returns:
        Dict: DataFrame详细信息
    
    调用样例:
    ```python
    # 获取DataFrame详细信息
    result = get_dataframe_info(
        variable_name="df_sales",
        session_id="session_a1b2c3d4"
    )
    
    # 检查加载的数据信息
    result = get_dataframe_info(
        variable_name="df_users",
        session_id="session_a1b2c3d4"
    )
    ```
    
    返回格式:
    成功时包含: success, variable_name, shape, columns, dtypes, memory_usage, null_counts, index_info
    memory_usage 包含总使用量和每列使用量
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        # 获取DataFrame对象
        df = session.shell.user_ns.get(variable_name)
        if df is None:
            return {
                "success": False,
                "error": f"Variable '{variable_name}' not found in session"
            }
        
        if not hasattr(df, 'shape') or not hasattr(df, 'dtypes'):
            return {
                "success": False,
                "error": f"Variable '{variable_name}' is not a DataFrame"
            }
        
        # 获取详细信息
        dtypes_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}
        memory_usage = df.memory_usage(deep=True)
        total_memory_mb = memory_usage.sum() / 1024 / 1024
        
        per_column_kb = {col: round(memory_usage[col] / 1024, 1) for col in df.columns}
        null_counts = df.isnull().sum().to_dict()
        
        # 索引信息
        index_info = {
            "type": type(df.index).__name__,
            "start": int(df.index[0]) if len(df.index) > 0 and hasattr(df.index[0], '__int__') else str(df.index[0]) if len(df.index) > 0 else None,
            "stop": int(df.index[-1]) if len(df.index) > 0 and hasattr(df.index[-1], '__int__') else str(df.index[-1]) if len(df.index) > 0 else None,
            "step": 1 if isinstance(df.index, pd.RangeIndex) else None
        }
        
        return {
            "success": True,
            "variable_name": variable_name,
            "shape": list(df.shape),
            "columns": list(df.columns),
            "dtypes": dtypes_dict,
            "memory_usage": {
                "total_mb": round(total_memory_mb, 2),
                "per_column_kb": per_column_kb
            },
            "null_counts": null_counts,
            "index_info": index_info
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get dataframe info: {str(e)}"
        }

@mcp.tool()
def preview_dataframe(
    variable_name: str,
    session_id: str,
    method: str = "head",
    n_rows: int = 5
) -> Dict[str, Any]:
    """
    预览 DataFrame 数据
    
    功能说明:
    - 预览DataFrame的数据内容
    - 支持头部、尾部、随机采样三种方式
    - 返回易读的记录格式
    
    Args:
        variable_name: DataFrame变量名
        session_id: 会话ID
        method: 预览方法 ("head", "tail", "sample")
        n_rows: 行数
    
    调用样例:
    ```python
    # 查看前5行
    result = preview_dataframe("df", "session_a1b2c3d4", "head", 5)
    
    # 随机采样10行
    result = preview_dataframe("df", "session_a1b2c3d4", "sample", 10)
    ```
    
    返回格式:
    成功时包含: success, variable_name, method, n_rows, data (记录列表), total_rows
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        # 获取DataFrame对象
        df = session.shell.user_ns.get(variable_name)
        if df is None:
            return {
                "success": False,
                "error": f"Variable '{variable_name}' not found in session"
            }
        
        if not hasattr(df, 'shape'):
            return {
                "success": False,
                "error": f"Variable '{variable_name}' is not a DataFrame"
            }
        
        # 根据方法获取数据
        if method == "head":
            preview_df = df.head(n_rows)
        elif method == "tail":
            preview_df = df.tail(n_rows)
        elif method == "sample":
            n_rows = min(n_rows, len(df))  # 确保不超过实际行数
            preview_df = df.sample(n_rows) if len(df) > 0 else df.head(0)
        else:
            return {
                "success": False,
                "error": f"Invalid method '{method}'. Use 'head', 'tail', or 'sample'"
            }
        
        # 转换为记录格式
        data = preview_df.to_dict('records')
        
        return {
            "success": True,
            "variable_name": variable_name,
            "method": method,
            "n_rows": len(preview_df),
            "data": data,
            "total_rows": len(df)
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to preview dataframe: {str(e)}"
        }

@mcp.tool()
def get_dataframe_summary(
    variable_name: str,
    session_id: str,
    include_categorical: bool = True
) -> Dict[str, Any]:
    """
    获取 DataFrame 统计摘要
    
    功能说明:
    - 获取DataFrame的统计摘要信息
    - 支持数值变量和分类变量统计
    - 提供describe()的结构化输出
    
    Args:
        variable_name: DataFrame变量名
        session_id: 会话ID
        include_categorical: 是否包含分类变量统计
    
    调用样例:
    ```python
    result = get_dataframe_summary("df", "session_a1b2c3d4", include_categorical=True)
    ```
    
    返回格式:
    成功时包含: success, variable_name, numeric_summary, categorical_summary (可选)
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        # 获取DataFrame对象
        df = session.shell.user_ns.get(variable_name)
        if df is None:
            return {
                "success": False,
                "error": f"Variable '{variable_name}' not found in session"
            }
        
        if not hasattr(df, 'describe'):
            return {
                "success": False,
                "error": f"Variable '{variable_name}' is not a DataFrame"
            }
        
        result = {
            "success": True,
            "variable_name": variable_name
        }
        
        # 数值变量统计
        numeric_df = df.select_dtypes(include=['number'])
        if len(numeric_df.columns) > 0:
            numeric_summary = {}
            desc = numeric_df.describe()
            for col in numeric_df.columns:
                numeric_summary[col] = desc[col].to_dict()
            result["numeric_summary"] = numeric_summary
        
        # 分类变量统计
        if include_categorical:
            categorical_df = df.select_dtypes(include=['object', 'category'])
            if len(categorical_df.columns) > 0:
                categorical_summary = {}
                for col in categorical_df.columns:
                    desc = df[col].describe()
                    categorical_summary[col] = {
                        "count": int(desc['count']),
                        "unique": int(desc['unique']),
                        "top": str(desc['top']),
                        "freq": int(desc['freq'])
                    }
                result["categorical_summary"] = categorical_summary
        
        return result
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get dataframe summary: {str(e)}"
        }

@mcp.tool()
def check_memory_usage(session_id: str) -> Dict[str, Any]:
    """
    查看会话的内存使用情况
    
    功能说明:
    - 分析会话中所有变量的内存使用情况
    - 按变量类型分组统计内存使用
    - 列出内存使用最多的变量
    - 提供系统内存状态信息
    - 用于内存优化和性能调试
    
    Args:
        session_id: 会话ID
    
    Returns:
        Dict: 内存使用详细信息
    
    调用样例:
    ```python
    # 检查会话内存使用
    result = check_memory_usage(session_id="session_a1b2c3d4")
    
    # 在数据加载后检查内存
    load_csv_file("large_data.csv", "session_a1b2c3d4")
    result = check_memory_usage(session_id="session_a1b2c3d4")
    ```
    
    返回格式:
    成功时包含: success, session_id, total_memory_mb, breakdown (按类型分组), top_variables (最大变量列表), system_memory (系统内存信息)
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        memory_info = session.get_memory_info()
        
        return {
            "success": True,
            "session_id": session_id,
            "total_memory_mb": memory_info['total_memory_mb'],
            "breakdown": memory_info['breakdown'],
            "top_variables": memory_info['top_variables'],
            "system_memory": memory_info['system_memory']
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check memory usage: {str(e)}"
        }

@mcp.tool()
def get_variable_info(
    variable_name: str,
    session_id: str,
    include_preview: bool = True
) -> Dict[str, Any]:
    """
    获取指定变量的详细信息
    
    功能说明:
    - 获取任意类型变量的详细信息
    - 支持 DataFrame, numpy 数组, 列表, 字典等所有 Python 对象
    - 提供类型信息、大小信息、内存使用等
    - 可选择包含变量内容预览
    - 特别优化对数据科学对象的信息展示
    
    Args:
        variable_name: 会话中变量的名称
        session_id: 会话ID
        include_preview: 是否包含内容预览（默认 True）
    
    Returns:
        Dict: 变量详细信息
    
    调用样例:
    ```python
    # 获取DataFrame变量信息
    result = get_variable_info(
        variable_name="df_sales",
        session_id="session_a1b2c3d4",
        include_preview=True
    )
    
    # 获取列表变量信息，不包含预览
    result = get_variable_info(
        variable_name="my_list",
        session_id="session_a1b2c3d4",
        include_preview=False
    )
    
    # 获取numpy数组信息
    result = get_variable_info(
        variable_name="numpy_array",
        session_id="session_a1b2c3d4"
    )
    ```
    
    返回格式:
    成功时包含: success, variable_name, type, size_info, content_preview (可选), additional_info (类型相关信息)
    size_info 包含: size_bytes, memory_mb, shape (如适用), element_count (如适用)
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        # 获取变量对象
        var = session.shell.user_ns.get(variable_name)
        if var is None:
            return {
                "success": False,
                "error": f"Variable '{variable_name}' not found in session"
            }
        
        var_type = type(var).__name__
        size_bytes = sys.getsizeof(var)
        
        result = {
            "success": True,
            "variable_name": variable_name,
            "type": f"{type(var).__module__}.{var_type}" if hasattr(type(var), '__module__') else var_type,
            "size_info": {
                "size_bytes": size_bytes,
                "memory_mb": round(size_bytes / 1024 / 1024, 3)
            }
        }
        
        # 特殊处理不同类型
        if hasattr(var, 'shape') and hasattr(var, 'dtypes'):  # DataFrame
            result["size_info"].update({
                "shape": list(var.shape),
                "element_count": var.size
            })
            result["additional_info"] = {
                "columns": list(var.columns),
                "dtypes": {col: str(dtype) for col, dtype in var.dtypes.items()}
            }
            if include_preview:
                result["content_preview"] = str(var.head())
                
        elif hasattr(var, 'shape'):  # numpy array
            result["size_info"].update({
                "shape": list(var.shape),
                "element_count": var.size
            })
            result["additional_info"] = {
                "dtype": str(var.dtype) if hasattr(var, 'dtype') else None
            }
            if include_preview:
                result["content_preview"] = str(var)
                
        elif isinstance(var, (list, tuple, dict, set)):
            result["size_info"]["element_count"] = len(var)
            if include_preview:
                preview = str(var)
                if len(preview) > 200:
                    preview = preview[:200] + "..."
                result["content_preview"] = preview
                
        else:
            if include_preview:
                preview = str(var)
                if len(preview) > 200:
                    preview = preview[:200] + "..."
                result["content_preview"] = preview
        
        return result
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get variable info: {str(e)}"
        }

@mcp.tool()
def sample_column_data(
    variable_name: str,
    column_name: str,
    session_id: str,
    method: str = "mixed",
    sample_size: int = 20,
    max_text_length: int = 100,
    include_stats: bool = True
) -> Dict[str, Any]:
    """
    智能采样查看 DataFrame 列数据
    
    功能说明:
    - 智能采样DataFrame中指定列的数据，避免上下文被填满
    - 支持多种采样方式：头部、尾部、随机、唯一值、混合
    - 自动截断过长的文本内容
    - 提供详细的统计信息
    - 特别适合大数据集的列数据探索
    
    Args:
        variable_name: DataFrame变量名
        column_name: 列名
        session_id: 会话ID
        method: 采样方法 ("head", "tail", "random", "unique", "mixed")
        sample_size: 采样数量 (默认20)
        max_text_length: 文本最大长度 (默认100字符)
        include_stats: 是否包含统计信息
    
    Returns:
        Dict: 列数据采样结果
    
    调用样例:
    ```python
    # 混合采样查看列数据
    result = sample_column_data(
        variable_name="df_sales",
        column_name="product_name",
        session_id="session_a1b2c3d4",
        method="mixed",
        sample_size=20
    )
    
    # 查看唯一值
    result = sample_column_data(
        variable_name="df_sales", 
        column_name="category",
        session_id="session_a1b2c3d4",
        method="unique",
        sample_size=50
    )
    
    # 随机采样数值列
    result = sample_column_data(
        variable_name="df_sales",
        column_name="price", 
        session_id="session_a1b2c3d4",
        method="random",
        sample_size=30
    )
    ```
    
    返回格式:
    成功时包含: success, variable_name, column_name, method, sample_data, statistics, total_count
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        # 获取DataFrame对象
        df = session.shell.user_ns.get(variable_name)
        if df is None:
            return {
                "success": False,
                "error": f"Variable '{variable_name}' not found in session"
            }
        
        if not hasattr(df, 'shape') or not hasattr(df, 'columns'):
            return {
                "success": False,
                "error": f"Variable '{variable_name}' is not a DataFrame"
            }
        
        if column_name not in df.columns:
            return {
                "success": False,
                "error": f"Column '{column_name}' not found in DataFrame. Available columns: {list(df.columns)}"
            }
        
        column_data = df[column_name]
        total_count = len(column_data)
        
        # 基本统计信息
        stats = {}
        if include_stats:
            stats = {
                "total_count": total_count,
                "null_count": int(column_data.isnull().sum()),
                "non_null_count": int(column_data.count()),
                "data_type": str(column_data.dtype)
            }
            
            # 唯一值统计
            unique_values = column_data.dropna().unique()
            stats["unique_count"] = len(unique_values)
            stats["duplicate_count"] = total_count - len(unique_values) - stats["null_count"]
            
            # 数值类型的特殊统计
            if column_data.dtype in ['int64', 'float64', 'int32', 'float32']:
                non_null_data = column_data.dropna()
                if len(non_null_data) > 0:
                    stats["numeric_stats"] = {
                        "min": float(non_null_data.min()),
                        "max": float(non_null_data.max()),
                        "mean": float(non_null_data.mean()),
                        "median": float(non_null_data.median()),
                        "std": float(non_null_data.std()) if len(non_null_data) > 1 else 0.0
                    }
            
            # 文本类型的特殊统计
            elif column_data.dtype == 'object':
                non_null_data = column_data.dropna().astype(str)
                if len(non_null_data) > 0:
                    text_lengths = non_null_data.str.len()
                    stats["text_stats"] = {
                        "min_length": int(text_lengths.min()),
                        "max_length": int(text_lengths.max()),
                        "avg_length": float(text_lengths.mean())
                    }
        
        # 数据采样
        sample_data = []
        actual_sample_size = min(sample_size, total_count)
        
        if method == "head":
            sampled = column_data.head(actual_sample_size)
        elif method == "tail":
            sampled = column_data.tail(actual_sample_size)
        elif method == "random":
            sampled = column_data.sample(n=actual_sample_size) if total_count > 0 else column_data.head(0)
        elif method == "unique":
            # 获取唯一值
            unique_values = column_data.dropna().unique()
            if len(unique_values) > actual_sample_size:
                # 如果唯一值太多，随机选择
                import numpy as np
                selected_indices = np.random.choice(len(unique_values), actual_sample_size, replace=False)
                sampled_values = unique_values[selected_indices]
            else:
                sampled_values = unique_values
            
            # 创建一个Series用于统一处理
            sampled = pd.Series(sampled_values)
        elif method == "mixed":
            # 混合采样：头部、尾部、随机各占一部分
            third = actual_sample_size // 3
            remainder = actual_sample_size % 3
            
            head_size = third + (1 if remainder > 0 else 0)
            tail_size = third + (1 if remainder > 1 else 0)
            random_size = third
            
            samples = []
            if head_size > 0:
                samples.extend(column_data.head(head_size).tolist())
            if tail_size > 0:
                samples.extend(column_data.tail(tail_size).tolist())
            if random_size > 0 and total_count > head_size + tail_size:
                # 避免重复采样已经在头部和尾部的数据
                middle_data = column_data.iloc[head_size:-tail_size] if tail_size > 0 else column_data.iloc[head_size:]
                if len(middle_data) > 0:
                    random_samples = middle_data.sample(n=min(random_size, len(middle_data)))
                    samples.extend(random_samples.tolist())
            
            sampled = pd.Series(samples)
        else:
            return {
                "success": False,
                "error": f"Invalid method '{method}'. Use 'head', 'tail', 'random', 'unique', or 'mixed'"
            }
        
        # 处理采样数据，截断过长的文本
        for idx, value in sampled.items():
            processed_value = value
            
            # 处理空值
            if pd.isna(value):
                processed_value = None
            else:
                # 转换为字符串并截断
                str_value = str(value)
                if len(str_value) > max_text_length:
                    processed_value = str_value[:max_text_length] + "..."
                else:
                    processed_value = str_value
            
            sample_data.append({
                "index": int(idx) if pd.notna(idx) and hasattr(idx, '__int__') else str(idx),
                "value": processed_value,
                "original_type": type(value).__name__
            })
        
        result = {
            "success": True,
            "variable_name": variable_name,
            "column_name": column_name,
            "method": method,
            "total_count": total_count,
            "sample_size": len(sample_data),
            "sample_data": sample_data
        }
        
        if include_stats:
            result["statistics"] = stats
        
        return result
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to sample column data: {str(e)}"
        }

@mcp.tool()
def clear_variables(
    session_id: str,
    variable_names: Optional[List[str]] = None,
    clear_all: bool = False,
    keep_imports: bool = True
) -> Dict[str, Any]:
    """
    清理指定变量或全部变量
    
    功能说明:
    - 清理会话中的指定变量或全部变量
    - 释放内存空间
    - 可选择保留导入的模块
    
    Args:
        session_id: 会话ID
        variable_names: 要清理的变量名列表
        clear_all: 是否清理所有变量
        keep_imports: 清理全部时是否保留导入的模块
    
    调用样例:
    ```python
    # 清理指定变量
    result = clear_variables("session_a1b2c3d4", ["df1", "df2"])
    
    # 清理所有变量，保留导入
    result = clear_variables("session_a1b2c3d4", clear_all=True, keep_imports=True)
    ```
    
    返回格式:
    成功时包含: success, cleared_variables (列表), memory_freed_mb, remaining_variables
    失败时包含: success, error
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        initial_memory = session._get_memory_usage()
        cleared_variables = []
        
        if clear_all:
            # 清理所有用户变量
            user_ns = session.shell.user_ns
            to_delete = []
            
            for name in user_ns:
                if not name.startswith('_') and name not in ['In', 'Out', 'get_ipython', 'exit', 'quit']:
                    # 如果保留导入，跳过模块类型的变量
                    if keep_imports and hasattr(user_ns[name], '__module__'):
                        var_type = type(user_ns[name]).__name__
                        if 'module' in var_type.lower():
                            continue
                    to_delete.append(name)
            
            for name in to_delete:
                if name in user_ns:
                    del user_ns[name]
                    cleared_variables.append(name)
                    
        elif variable_names:
            # 清理指定变量
            user_ns = session.shell.user_ns
            for name in variable_names:
                if name in user_ns:
                    del user_ns[name]
                    cleared_variables.append(name)
        else:
            return {
                "success": False,
                "error": "Must specify either variable_names or set clear_all=True"
            }
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        final_memory = session._get_memory_usage()
        memory_freed = initial_memory - final_memory
        
        variables_after = session.get_variables()
        
        return {
            "success": True,
            "cleared_variables": cleared_variables,
            "memory_freed_mb": round(memory_freed, 2),
            "remaining_variables": len(variables_after)
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to clear variables: {str(e)}"
        }

if __name__ == "__main__":
    # 启动MCP服务器
    mcp.run(transport="stdio")