# IPython 数据分析 MCP 服务器 / IPython Data Analysis MCP Server

[🇨🇳 中文](#中文版本) | [🇺🇸 English](#english-version)

---

## 中文版本

基于真正 IPython 内核的轻量级数据分析 MCP (Model Context Protocol) 工具，提供完整的交互式 Python 数据分析环境，支持会话管理、数据加载、实时数据查看等核心功能。

### 🚀 核心特性

- **真正的 IPython 环境**: 基于 IPython InteractiveShell，支持所有 IPython 功能
- **多会话管理**: 独立的会话空间，变量隔离，持久化状态
- **智能数据加载**: 支持 CSV/Excel/JSON，自动编码检测，智能变量命名
- **实时监控**: 内存使用监控、变量管理、执行历史追踪
- **完整功能支持**: Python代码、IPython魔法命令、系统命令执行
- **智能采样**: 大数据集友好的列数据查看，避免上下文溢出

### 📋 功能清单

#### 17个核心工具函数

1. **会话管理**
   - `create_ipython_session` - 创建新的 IPython 会话
   - `list_ipython_sessions` - 列出所有活跃会话
   - `get_session_status` - 获取会话详细状态
   - `delete_ipython_session` - 删除指定会话

2. **代码执行**
   - `execute_code` - 执行 Python 代码、魔法命令、系统命令
   - `get_execution_history` - 获取执行历史记录

3. **数据加载**
   - `load_csv_file` - 加载 CSV 文件（自动编码检测）
   - `load_excel_file` - 加载 Excel 文件（支持 .xlsx/.xls）
   - `load_json_file` - 加载 JSON 文件

4. **数据操作与查看**
   - `list_dataframes` - 列出会话中所有 DataFrame
   - `get_dataframe_info` - 获取 DataFrame 详细信息
   - `preview_dataframe` - 预览 DataFrame 数据
   - `get_dataframe_summary` - 获取统计摘要
   - `sample_column_data` - 智能采样查看列数据

5. **内存与变量管理**
   - `check_memory_usage` - 检查内存使用情况
   - `get_variable_info` - 获取变量详细信息
   - `clear_variables` - 清理变量释放内存

### 🛠️ 安装配置

#### 方法一：使用 uvx 直接运行（推荐）

无需克隆项目，直接使用 uvx 从 GitHub 运行：

```bash
# 安装 uvx（如果还没有安装）
pip install uvx

# 直接运行 MCP 服务器
uvx --from git+https://github.com/Hillyess/dataHill.git DATA_MCP.py
```

#### 方法二：本地安装开发

```bash
# 1. 克隆项目
git clone git@github.com:Hillyess/dataHill.git
cd dataHill

# 2. 创建虚拟环境
conda create -n data-analyzer python=3.10
conda activate data-analyzer

# 3. 安装依赖
pip install -r requirements.txt

# 4. 测试安装
python DATA_MCP.py
```

#### 配置 MCP 客户端

##### Claude Desktop 配置

编辑 Claude Desktop 配置文件：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**推荐配置（使用 uvx）**：
```json
{
  "mcpServers": {
    "dataHill": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Hillyess/dataHill.git",
        "DATA_MCP.py"
      ]
    }
  }
}
```

**本地开发配置**（如果使用方法二）：
```json
{
  "mcpServers": {
    "dataHill": {
      "command": "python",
      "args": ["/path/to/your/DATA_MCP.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

### 📖 使用指南

#### 基本工作流程

```python
# 1. 创建会话
create_ipython_session()
# 返回: {"success": true, "session_id": "session_a1b2c3d4", ...}

# 2. 加载数据
load_csv_file("data.csv", "session_a1b2c3d4", "df")

# 3. 查看数据信息
get_dataframe_info("df", "session_a1b2c3d4")

# 4. 智能采样查看数据
sample_column_data("df", "column_name", "session_a1b2c3d4", method="mixed", sample_size=20)

# 5. 执行分析
execute_code("df.describe()", "session_a1b2c3d4")

# 6. 内存监控
check_memory_usage("session_a1b2c3d4")

# 7. 清理会话
delete_ipython_session("session_a1b2c3d4")
```

### 🔧 系统要求

- **Python**: 3.8+
- **内存**: 建议 4GB+ （取决于数据规模）
- **操作系统**: Windows/macOS/Linux
- **MCP 客户端**: Claude Desktop 或其他支持 stdio 的 MCP 客户端

### 📦 依赖项

#### 核心依赖
- `fastmcp>=0.5.0` - MCP 服务器框架
- `ipython>=8.0.0` - IPython 交互式环境
- `pandas>=2.0.0` - 数据处理和分析
- `numpy>=1.24.0` - 数值计算基础库

#### 数据支持
- `openpyxl>=3.1.0` - Excel .xlsx 文件支持
- `xlrd>=2.0.0` - Excel .xls 文件支持

#### 系统监控
- `psutil>=5.9.0` - 内存和系统监控

### 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

### 🙋‍♂️ 支持与反馈

- **问题报告**: [GitHub Issues](https://github.com/Hillyess/dataHill/issues)
- **功能请求**: [GitHub Discussions](https://github.com/Hillyess/dataHill/discussions)

---

## English Version

A lightweight data analysis MCP (Model Context Protocol) tool based on real IPython kernel, providing complete interactive Python data analysis environment with session management, data loading, real-time data viewing and other core functions.

### 🚀 Core Features

- **Real IPython Environment**: Based on IPython InteractiveShell, supports all IPython features
- **Multi-Session Management**: Independent session spaces, variable isolation, persistent state
- **Intelligent Data Loading**: Supports CSV/Excel/JSON, automatic encoding detection, smart variable naming
- **Real-time Monitoring**: Memory usage monitoring, variable management, execution history tracking
- **Complete Feature Support**: Python code, IPython magic commands, system command execution
- **Smart Sampling**: Large dataset friendly column data viewing, avoiding context overflow

### 📋 Feature List

#### 17 Core Tool Functions

1. **Session Management**
   - `create_ipython_session` - Create new IPython session
   - `list_ipython_sessions` - List all active sessions
   - `get_session_status` - Get detailed session status
   - `delete_ipython_session` - Delete specified session

2. **Code Execution**
   - `execute_code` - Execute Python code, magic commands, system commands
   - `get_execution_history` - Get execution history

3. **Data Loading**
   - `load_csv_file` - Load CSV files (automatic encoding detection)
   - `load_excel_file` - Load Excel files (supports .xlsx/.xls)
   - `load_json_file` - Load JSON files

4. **Data Operations & Viewing**
   - `list_dataframes` - List all DataFrames in session
   - `get_dataframe_info` - Get detailed DataFrame information
   - `preview_dataframe` - Preview DataFrame data
   - `get_dataframe_summary` - Get statistical summary
   - `sample_column_data` - Smart sampling for column data viewing

5. **Memory & Variable Management**
   - `check_memory_usage` - Check memory usage
   - `get_variable_info` - Get detailed variable information
   - `clear_variables` - Clear variables to free memory

### 🛠️ Installation & Configuration

#### Method 1: Direct Run with uvx (Recommended)

No need to clone the project, run directly from GitHub using uvx:

```bash
# Install uvx (if not already installed)
pip install uvx

# Run MCP server directly
uvx --from git+https://github.com/Hillyess/dataHill.git DATA_MCP.py
```

#### Method 2: Local Installation for Development

```bash
# 1. Clone project
git clone git@github.com:Hillyess/dataHill.git
cd dataHill

# 2. Create virtual environment
conda create -n data-analyzer python=3.10
conda activate data-analyzer

# 3. Install dependencies
pip install -r requirements.txt

# 4. Test installation
python DATA_MCP.py
```

##### Configure MCP Client

##### Claude Desktop Configuration

Edit Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Recommended Configuration (using uvx)**:
```json
{
  "mcpServers": {
    "dataHill": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Hillyess/dataHill.git",
        "DATA_MCP.py"
      ]
    }
  }
}
```

**Local Development Configuration** (if using Method 2):
```json
{
  "mcpServers": {
    "dataHill": {
      "command": "python",
      "args": ["/path/to/your/DATA_MCP.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

### 📖 Usage Guide

#### Basic Workflow

```python
# 1. Create session
create_ipython_session()
# Returns: {"success": true, "session_id": "session_a1b2c3d4", ...}

# 2. Load data
load_csv_file("data.csv", "session_a1b2c3d4", "df")

# 3. View data information
get_dataframe_info("df", "session_a1b2c3d4")

# 4. Smart sampling for data viewing
sample_column_data("df", "column_name", "session_a1b2c3d4", method="mixed", sample_size=20)

# 5. Execute analysis
execute_code("df.describe()", "session_a1b2c3d4")

# 6. Memory monitoring
check_memory_usage("session_a1b2c3d4")

# 7. Clean up session
delete_ipython_session("session_a1b2c3d4")
```

### 🔧 System Requirements

- **Python**: 3.8+
- **Memory**: Recommended 4GB+ (depends on data scale)
- **Operating System**: Windows/macOS/Linux
- **MCP Client**: Claude Desktop or other stdio-supported MCP clients

### 📦 Dependencies

#### Core Dependencies
- `fastmcp>=0.5.0` - MCP server framework
- `ipython>=8.0.0` - IPython interactive environment
- `pandas>=2.0.0` - Data processing and analysis
- `numpy>=1.24.0` - Numerical computation foundation

#### Data Support
- `openpyxl>=3.1.0` - Excel .xlsx file support
- `xlrd>=2.0.0` - Excel .xls file support

#### System Monitoring
- `psutil>=5.9.0` - Memory and system monitoring

### 🤝 Contributing

1. Fork this project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🙋‍♂️ Support & Feedback

- **Issue Reports**: [GitHub Issues](https://github.com/Hillyess/dataHill/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/Hillyess/dataHill/discussions)

---

⭐ If this project helps you, please give us a Star!