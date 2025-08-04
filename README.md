# dataHill

An MCP service that automates data analysis through IPython sessions.

IPython 数据分析 MCP 设计文档

# 1. 项目概述

## 1.1 项目简介

  基于真正 IPython 内核的轻量级数据分析 MCP (Model Context Protocol) 工具，提供完整的交互式 Python 数据分析环境，支持会话管理、数据加载、实时数据查看等核心功能。

## 1.2 设计目标

  - 提供真正的 IPython 交互式环境
  - 支持多会话隔离和管理
  - 便捷的数据文件加载功能
  - 实时的内存数据状态查看
  - 支持 Python 代码、魔法命令、系统命令执行

## 1.3 核心特性

  - ✅ 基于 IPython InteractiveShell 的真实环境
  - ✅ 多会话隔离和持久化状态
  - ✅ 支持 CSV/Excel/JSON 数据加载
  - ✅ 实时内存和变量监控
  - ✅ 完整的 IPython 功能（魔法命令、系统命令）
  - ✅ MCP stdio 协议兼容

# 2. 技术架构

## 2.1 整体架构

  ┌─────────────────────┐
  │   MCP Client        │ (Claude/其他大模型)
  │   (via stdio)       │
  └─────────┬───────────┘
            │ MCP Protocol
  ┌─────────▼───────────┐
  │   FastMCP Server    │
  │   - Tool Registry   │
  │   - Request Handler │
  └─────────┬───────────┘
            │
  ┌─────────▼───────────┐
  │ Session Manager     │
  │ - Multi Sessions    │
  │ - State Isolation   │
  └─────────┬───────────┘
            │
  ┌─────────▼───────────┐
  │ IPython Shells      │
  │ - Real IPython      │
  │ - Magic Commands    │
  │ - Shell Commands    │
  └─────────────────────┘

## 2.2 技术选型

  核心依赖

  fastmcp>=0.5.0          # MCP 服务器框架
  ipython>=8.0.0          # IPython 内核
  pandas>=2.0.0           # 数据处理
  numpy>=1.24.0           # 数值计算
  scikit-learn                 # 机器学习包
  openpyxl>=3.1.0         # Excel 支持
  psutil>=5.9.0           # 系统监控

  可选依赖

  matplotlib>=3.7.0       # 可视化
  seaborn>=0.12.0         # 统计可视化
  jupyter-client>=8.0.0   # Jupyter 协议支持

## 2.3 核心组件

### 2.3.1 会话管理器 (SessionManager)

  class IPythonSessionManager:
      def __init__(self):
          self.sessions: Dict[str, IPythonSession] = {}
          self.lock = threading.Lock()

      def create_session(self, session_id: str) -> IPythonSession
      def get_session(self, session_id: str) -> IPythonSession
      def delete_session(self, session_id: str) -> bool
      def list_sessions(self) -> List[SessionInfo]

### 2.3.2 IPython 会话 (IPythonSession)

  class IPythonSession:
      def __init__(self, session_id: str):
          self.session_id = session_id
          self.shell = InteractiveShell.instance()
          self.created_at = datetime.now()
          self.last_used = datetime.now()
          self.execution_count = 0

      def execute(self, code: str) -> ExecutionResult
      def get_variables(self) -> Dict[str, Any]
      def get_memory_usage(self) -> MemoryInfo

### 2.3.3 数据加载器 (DataLoader)

  class DataLoader:
      @staticmethod
      def load_csv(file_path: str, **kwargs) -> pd.DataFrame

      @staticmethod
      def load_excel(file_path: str, **kwargs) -> pd.DataFrame

      @staticmethod
      def load_json(file_path: str, **kwargs) -> pd.DataFrame

# 3. 函数规格说明

## 3.1 会话管理函数

### 3.1.1 create_ipython_session

  def create_ipython_session(
      session_id: Optional[str] = None,
      auto_import: bool = True
  ) -> Dict[str, Any]:
  功能: 创建新的 IPython 会话
  参数:
  - session_id: 会话ID，可选，不提供则自动生成
  - auto_import: 是否自动导入常用库 (pandas, numpy等)

  返回值:
  {
      "success": true,
      "session_id": "session_12345",
      "message": "IPython session created successfully",
      "auto_imported": ["pandas", "numpy", "matplotlib"]
  }

### 3.1.2 list_ipython_sessions

  def list_ipython_sessions() -> Dict[str, Any]:
  功能: 列出所有活跃的 IPython 会话
  返回值:
  {
      "success": true,
      "sessions": [
          {
              "session_id": "session_12345",
              "created_at": "2024-01-01T10:00:00",
              "last_used": "2024-01-01T10:30:00",
              "execution_count": 15,
              "memory_usage_mb": 128.5,
              "variable_count": 8
          }
      ],
      "total_sessions": 1
  }

### 3.1.3 get_session_status

  def get_session_status(session_id: str) -> Dict[str, Any]:
  功能: 获取指定会话的详细状态信息
  参数:
  - session_id: 会话ID

  返回值:
  {
      "success": true,
      "session_info": {
          "session_id": "session_12345",
          "status": "active",
          "created_at": "2024-01-01T10:00:00",
          "last_used": "2024-01-01T10:30:00",
          "execution_count": 15,
          "memory_usage": {
              "total_mb": 128.5,
              "variables_mb": 45.2,
              "system_mb": 83.3
          },
          "variable_summary": {
              "dataframes": 3,
              "lists": 2,
              "scalars": 5,
              "functions": 1
          }
      }
  }

### 3.1.4 delete_ipython_session

  def delete_ipython_session(session_id: str) -> Dict[str, Any]:
  功能: 删除指定的 IPython 会话
  参数:
  - session_id: 会话ID

  返回值:
  {
      "success": true,
      "message": "Session session_12345 deleted successfully"
  }

## 3.2 代码执行函数

### 3.2.1 execute_code

  def execute_code(
      code: str,
      session_id: str,
      capture_output: bool = True,
      timeout: int = 30
  ) -> Dict[str, Any]:
  功能: 在指定会话中执行代码
  支持类型:
  - Python代码: x = 1 + 1、import pandas as pd
  - 魔法命令: %timeit sum(range(100))、%matplotlib inline、%who
  - 命令行命令: !ls -la、!pip install numpy、!pwd

  参数:
  - code: 要执行的代码（支持多行）
  - session_id: 会话ID
  - capture_output: 是否捕获输出
  - timeout: 超时时间（秒）

  返回值:
  {
      "success": true,
      "execution_count": 16,
      "stdout": "Hello World\n",
      "stderr": "",
      "result": "None",
      "execution_time": 0.045,
      "memory_delta_mb": 2.1
  }

### 3.2.2 get_execution_history

  def get_execution_history(
      session_id: str,
      limit: int = 10,
      include_output: bool = False
  ) -> Dict[str, Any]:
  功能: 获取会话的执行历史
  参数:
  - session_id: 会话ID
  - limit: 返回的历史记录数量
  - include_output: 是否包含输出结果

  返回值:
  {
      "success": true,
      "history": [
          {
              "execution_count": 15,
              "timestamp": "2024-01-01T10:29:30",
              "code": "df.head()",
              "success": true,
              "execution_time": 0.012,
              "output": "..."
          }
      ],
      "total_executions": 15
  }

## 3.3 数据加载函数

### 3.3.1 load_csv_file

  def load_csv_file(
      file_path: str,
      session_id: str,
      variable_name: Optional[str] = None,
      encoding: str = "auto",
      **pandas_kwargs
  ) -> Dict[str, Any]:
  功能: 加载 CSV 文件到 DataFrame
  参数:
  - file_path: CSV文件路径
  - session_id: 会话ID
  - variable_name: 变量名，不提供则自动生成
  - encoding: 文件编码，"auto"为自动检测
  - **pandas_kwargs: 传递给 pandas.read_csv 的参数

  返回值:
  {
      "success": true,
      "variable_name": "df_data",
      "shape": [1000, 15],
      "columns": ["col1", "col2", "..."],
      "dtypes": {"col1": "int64", "col2": "object"},
      "memory_usage_mb": 12.5,
      "encoding_detected": "utf-8",
      "load_time": 0.234
  }

### 3.3.2 load_excel_file

  def load_excel_file(
      file_path: str,
      session_id: str,
      variable_name: Optional[str] = None,
      sheet_name: Union[str, int] = 0,
      **pandas_kwargs
  ) -> Dict[str, Any]:
  功能: 加载 Excel 文件到 DataFrame
  参数:
  - file_path: Excel文件路径
  - session_id: 会话ID
  - variable_name: 变量名，不提供则自动生成
  - sheet_name: 工作表名称或索引
  - **pandas_kwargs: 传递给 pandas.read_excel 的参数

### 3.3.3 load_json_file

  def load_json_file(
      file_path: str,
      session_id: str,
      variable_name: Optional[str] = None,
      **pandas_kwargs
  ) -> Dict[str, Any]:
  功能: 加载 JSON 文件到 DataFrame
  参数:
  - file_path: JSON文件路径
  - session_id: 会话ID
  - variable_name: 变量名，不提供则自动生成
  - **pandas_kwargs: 传递给 pandas.read_json 的参数

## 3.4 内存数据查看函数

### 3.4.1 list_dataframes

  def list_dataframes(session_id: str) -> Dict[str, Any]:
  功能: 列出会话中所有 DataFrame 变量
  返回值:
  {
      "success": true,
      "dataframes": [
          {
              "name": "df_sales",
              "shape": [1000, 8],
              "memory_mb": 15.2,
              "columns": ["date", "product", "sales", "..."]
          },
          {
              "name": "df_users",
              "shape": [500, 12],
              "memory_mb": 8.7,
              "columns": ["user_id", "name", "email", "..."]
          }
      ],
      "total_dataframes": 2,
      "total_memory_mb": 23.9
  }

### 3.4.2 get_dataframe_info

  def get_dataframe_info(
      variable_name: str,
      session_id: str
  ) -> Dict[str, Any]:
  功能: 获取指定 DataFrame 的详细信息
  返回值:
  {
      "success": true,
      "variable_name": "df_sales",
      "shape": [1000, 8],
      "columns": ["date", "product", "sales", "region", "..."],
      "dtypes": {
          "date": "datetime64[ns]",
          "product": "object",
          "sales": "float64",
          "region": "object"
      },
      "memory_usage": {
          "total_mb": 15.2,
          "per_column_kb": {
              "date": 7.8,
              "product": 3.2,
              "sales": 7.8,
              "region": 2.1
          }
      },
      "null_counts": {
          "date": 0,
          "product": 5,
          "sales": 12,
          "region": 0
      },
      "index_info": {
          "type": "RangeIndex",
          "start": 0,
          "stop": 1000,
          "step": 1
      }
  }

### 3.4.3 preview_dataframe

  def preview_dataframe(
      variable_name: str,
      session_id: str,
      method: str = "head",
      n_rows: int = 5
  ) -> Dict[str, Any]:
  功能: 预览 DataFrame 数据
  参数:
  - variable_name: DataFrame变量名
  - session_id: 会话ID
  - method: 预览方法 ("head", "tail", "sample")
  - n_rows: 行数

  返回值:
  {
      "success": true,
      "variable_name": "df_sales",
      "method": "head",
      "n_rows": 5,
      "data": [
          {"date": "2024-01-01", "product": "A", "sales": 100.0},
          {"date": "2024-01-02", "product": "B", "sales": 150.0}
      ],
      "total_rows": 1000
  }

### 3.4.4 get_dataframe_summary

  def get_dataframe_summary(
      variable_name: str,
      session_id: str,
      include_categorical: bool = True
  ) -> Dict[str, Any]:
  功能: 获取 DataFrame 统计摘要
  参数:
  - variable_name: DataFrame变量名
  - session_id: 会话ID
  - include_categorical: 是否包含分类变量统计

  返回值:
  {
      "success": true,
      "variable_name": "df_sales",
      "numeric_summary": {
          "sales": {
              "count": 988,
              "mean": 125.5,
              "std": 45.2,
              "min": 10.0,
              "25%": 85.0,
              "50%": 120.0,
              "75%": 160.0,
              "max": 300.0
          }
      },
      "categorical_summary": {
          "product": {
              "count": 995,
              "unique": 25,
              "top": "Product_A",
              "freq": 89
          }
      }
  }

### 3.4.5 check_memory_usage

  def check_memory_usage(session_id: str) -> Dict[str, Any]:
  功能: 查看会话的内存使用情况
  返回值:
  {
      "success": true,
      "session_id": "session_12345",
      "total_memory_mb": 156.7,
      "breakdown": {
          "dataframes": 98.5,
          "lists": 12.3,
          "scalars": 2.1,
          "functions": 1.2,
          "others": 42.6
      },
      "top_variables": [
          {"name": "df_large", "type": "DataFrame", "memory_mb": 45.2},
          {"name": "big_list", "type": "list", "memory_mb": 8.7}
      ],
      "system_memory": {
          "available_mb": 2048.5,
          "used_percent": 7.7
      }
  }

## 3.5 工具函数

### 3.5.1 get_variable_info

  def get_variable_info(
      variable_name: str,
      session_id: str,
      include_preview: bool = True
  ) -> Dict[str, Any]:
  功能: 获取指定变量的详细信息
  参数:
  - variable_name: 变量名
  - session_id: 会话ID
  - include_preview: 是否包含内容预览

  返回值:
  {
      "success": true,
      "variable_name": "my_variable",
      "type": "pandas.DataFrame",
      "size_info": {
          "shape": [1000, 8],
          "memory_mb": 15.2,
          "element_count": 8000
      },
      "content_preview": "   col1  col2  col3\n0     1     2     3\n...",
      "additional_info": {
          "columns": ["col1", "col2", "col3"],
          "dtypes": {"col1": "int64", "col2": "float64"}
      }
  }

### 3.5.2 clear_variables

  def clear_variables(
      session_id: str,
      variable_names: Optional[List[str]] = None,
      clear_all: bool = False,
      keep_imports: bool = True
  ) -> Dict[str, Any]:
  功能: 清理指定变量或全部变量
  参数:
  - session_id: 会话ID
  - variable_names: 要清理的变量名列表
  - clear_all: 是否清理所有变量
  - keep_imports: 清理全部时是否保留导入的模块

  返回值:
  {
      "success": true,
      "cleared_variables": ["df1", "df2", "temp_list"],
      "memory_freed_mb": 45.7,
      "remaining_variables": 12
  }

# 4. 实现方案

## 4.1 项目结构

  ipython_data_mcp/
  ├── main.py                 # MCP 服务器入口
  ├── session_manager.py      # 会话管理器
  ├── ipython_session.py      # IPython 会话封装
  ├── data_loader.py          # 数据加载器
  ├── memory_monitor.py       # 内存监控器
  ├── utils/
  │   ├── __init__.py
  │   ├── encoding_detector.py
  │   ├── type_analyzer.py
  │   └── formatters.py
  ├── models/
  │   ├── __init__.py
  │   ├── responses.py        # 响应数据模型
  │   └── session_info.py     # 会话信息模型
  ├── tests/
  │   ├── test_session.py
  │   ├── test_data_loader.py
  │   └── test_integration.py
  ├── requirements.txt
  └── README.md

## 4.2 MCP 服务器配置

  {
    "mcpServers": {
      "ipython-data-analyzer": {
        "command": "python",
        "args": ["-m", "ipython_data_mcp.main"],
        "cwd": "/path/to/ipython_data_mcp",
        "env": {
          "PYTHONPATH": "/path/to/ipython_data_mcp"
        }
      }
    }
  }

## 4.3 启动方式

  # 开发模式
  python -m ipython_data_mcp.main

  # 生产模式
  python -m ipython_data_mcp.main --log-level INFO

## 4.4 错误处理策略

  - 会话不存在：返回明确错误信息
  - 代码执行失败：捕获异常并返回错误详情
  - 文件读取失败：提供编码建议和修复方案
  - 内存不足：提供内存清理建议
  - 超时处理：支持长时间运行的代码中断

## 4.5 性能优化

  - 会话复用：避免重复创建 IPython 实例
  - 延迟加载：按需加载数据处理库
  - 内存监控：实时监控并提供清理建议
  - 结果缓存：缓存频繁查询的结果

# 5. 使用示例

## 5.1 完整工作流程

  # 1. 创建会话
  response = create_ipython_session()
  session_id = response["session_id"]

  # 2. 加载数据
  load_csv_file("sales_data.csv", session_id, "df_sales")

  # 3. 查看数据信息
  get_dataframe_info("df_sales", session_id)

  # 4. 执行分析
  execute_code("""
  # 基本统计
  print(df_sales.describe())

  # 分组分析
  result = df_sales.groupby('region')['sales'].agg(['sum', 'mean'])
  print(result)
  """, session_id)

  # 5. 内存监控
  check_memory_usage(session_id)

  # 6. 清理完成
  delete_ipython_session(session_id)

## 5.2 与大模型集成示例

  User: 帮我分析这个销售数据文件
  Assistant: 我来帮你分析销售数据。首先创建一个分析会话：

  [调用 create_ipython_session]
  [调用 load_csv_file with "sales_data.csv"]
  [调用 get_dataframe_info]

  数据已成功加载！这是一个包含1000行、8列的销售数据集...

  User: 看看各地区的销售情况
  Assistant: [调用 execute_code with groupby analysis]

  各地区销售分析结果如下：
  - 华东地区：平均销售额 ¥125,000
  - 华南地区：平均销售额 ¥98,000
  ...

# 6. 测试计划

## 6.1 单元测试

  - 会话管理功能测试
  - 数据加载功能测试
  - 代码执行功能测试
  - 内存监控功能测试

## 6.2 集成测试

  - MCP 协议兼容性测试
  - 多会话并发测试
  - 大文件加载测试
  - 长时间运行稳定性测试

## 6.3 性能测试

  - 内存使用效率测试
  - 代码执行性能测试
  - 会话切换延迟测试
  - 并发处理能力测试

  这个设计文档涵盖了完整的技术方案和实现细节，确认无误后我们可以开始编码实现。
