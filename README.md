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

#### 1. 克隆项目

```bash
git clone git@github.com:Hillyess/dataHill.git
cd dataHill
```

#### 2. 创建虚拟环境

```bash
# 使用 conda
conda create -n data-analyzer python=3.10
conda activate data-analyzer

# 或使用 venv
python -m venv data-analyzer
source data-analyzer/bin/activate  # Linux/macOS
# 或 data-analyzer\Scripts\activate  # Windows
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 测试安装

```bash
python DATA_MCP.py
```

#### 5. 配置 MCP 客户端

##### Claude Desktop 配置

编辑 Claude Desktop 配置文件：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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

### 🎯 未来开发计划 - 多智能体系统

#### 阶段一：基础智能体框架 (3个月)
- [ ] **数据分析专家智能体**
  - 自动数据探索和质量评估
  - 智能特征工程建议
  - 自动化EDA报告生成
  
- [ ] **可视化专家智能体** 
  - 智能图表类型推荐
  - 自动化可视化生成
  - 交互式仪表板创建
  
- [ ] **统计分析专家智能体**
  - 自动假设检验选择
  - 统计显著性分析
  - A/B测试分析自动化

#### 阶段二：协作智能体生态 (6个月)
- [ ] **智能体协作框架**
  - 任务分解和分配机制
  - 智能体间通信协议
  - 结果整合和验证系统
  
- [ ] **机器学习专家智能体**
  - 自动模型选择和调优
  - 特征重要性分析
  - 模型解释和诊断
  
- [ ] **报告生成专家智能体**
  - 自动化分析报告撰写
  - 业务洞察提取
  - 多格式报告输出

#### 阶段三：高级智能体功能 (9个月)
- [ ] **数据清洗专家智能体**
  - 异常值检测和处理
  - 缺失值填充策略
  - 数据质量评分系统
  
- [ ] **时间序列专家智能体**
  - 趋势和季节性分析
  - 预测模型构建
  - 异常检测和预警
  
- [ ] **业务分析专家智能体**
  - KPI指标体系构建
  - 业务逻辑验证
  - 决策支持建议

#### 阶段四：企业级智能体平台 (12个月)
- [ ] **智能体编排平台**
  - 可视化智能体工作流设计
  - 任务调度和资源管理
  - 性能监控和优化
  
- [ ] **自定义智能体构建器**
  - 领域专家智能体快速创建
  - 智能体能力扩展机制
  - 知识库集成和管理
  
- [ ] **分布式智能体系统**
  - 多节点智能体部署
  - 负载均衡和容错机制
  - 企业级安全和权限管理

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

#### 1. Clone Project

```bash
git clone git@github.com:Hillyess/dataHill.git
cd dataHill
```

#### 2. Create Virtual Environment

```bash
# Using conda
conda create -n data-analyzer python=3.10
conda activate data-analyzer

# Or using venv
python -m venv data-analyzer
source data-analyzer/bin/activate  # Linux/macOS
# or data-analyzer\Scripts\activate  # Windows
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Test Installation

```bash
python DATA_MCP.py
```

#### 5. Configure MCP Client

##### Claude Desktop Configuration

Edit Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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

### 🎯 Future Development Plan - Multi-Agent System

#### Phase 1: Basic Agent Framework (3 months)
- [ ] **Data Analysis Expert Agent**
  - Automated data exploration and quality assessment
  - Intelligent feature engineering suggestions
  - Automated EDA report generation
  
- [ ] **Visualization Expert Agent**
  - Smart chart type recommendations
  - Automated visualization generation
  - Interactive dashboard creation
  
- [ ] **Statistical Analysis Expert Agent**
  - Automatic hypothesis test selection
  - Statistical significance analysis
  - A/B testing automation

#### Phase 2: Collaborative Agent Ecosystem (6 months)
- [ ] **Agent Collaboration Framework**
  - Task decomposition and assignment mechanisms
  - Inter-agent communication protocols
  - Result integration and validation systems
  
- [ ] **Machine Learning Expert Agent**
  - Automatic model selection and tuning
  - Feature importance analysis
  - Model interpretation and diagnostics
  
- [ ] **Report Generation Expert Agent**
  - Automated analysis report writing
  - Business insight extraction
  - Multi-format report output

#### Phase 3: Advanced Agent Features (9 months)
- [ ] **Data Cleaning Expert Agent**
  - Outlier detection and handling
  - Missing value imputation strategies
  - Data quality scoring system
  
- [ ] **Time Series Expert Agent**
  - Trend and seasonality analysis
  - Forecasting model construction
  - Anomaly detection and alerting
  
- [ ] **Business Analysis Expert Agent**
  - KPI metric system construction
  - Business logic validation
  - Decision support recommendations

#### Phase 4: Enterprise Agent Platform (12 months)
- [ ] **Agent Orchestration Platform**
  - Visual agent workflow design
  - Task scheduling and resource management
  - Performance monitoring and optimization
  
- [ ] **Custom Agent Builder**
  - Rapid domain expert agent creation
  - Agent capability extension mechanisms
  - Knowledge base integration and management
  
- [ ] **Distributed Agent System**
  - Multi-node agent deployment
  - Load balancing and fault tolerance
  - Enterprise-grade security and permission management

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