# pyStateView v1.0

## 1. Library定位 / 设计目标 / 核心价值
pyStateView 专注于 **离散状态随时间变化** 的工业可视化，面向 MCU/DSP 监控、SCADA 上位机、状态机调试等场景。库仅展示**实际采集的状态事实**，不进行预测、不插值、不平滑，确保工程可信性。核心价值：
- 工业风格、高可读性、明确的状态阶梯显示
- 事件数据驱动，状态结束由下一事件隐式决定
- 可嵌入 PyQt5 项目，支持实时 append 与渲染解耦

## 2. PhaseFlow 控件说明
PhaseFlow 用于显示状态随时间变化的阶梯块（Phase Flow）。

### 2.1 事件数据格式
```python
Event = {
    "timestamp": float,  # 秒或毫秒
    "state_id": str,     # 状态枚举或字符串
    "extra": dict        # 可选
}
```

### 2.2 基本使用示例
```python
from pyStateView.timeline.phase_flow import PhaseFlow

flow = PhaseFlow()
flow.append_event(timestamp=0.0, state_id="STOP")
flow.append_event(timestamp=1.2, state_id="LOW")
flow.append_event(timestamp=2.5, state_id="HIGH")
```

### 2.3 交互说明
- 滚轮 + Ctrl：时间轴缩放
- 水平滚动条：历史回看
- Hover：显示时间戳、状态、持续时间、extra

## 3. 扩展控件说明
### 3.1 StateIndicator
显示当前状态，可配置颜色与报警闪烁。

```python
from pyStateView.widgets.state_indicator import StateIndicator
indicator = StateIndicator()
indicator.set_state("HIGH")
```

### 3.2 StateDistributionBar
统计指定时间范围内各状态占比。

```python
from pyStateView.widgets.state_distribution import StateDistributionBar
bar = StateDistributionBar()
bar.update_from_events(flow.model.events)
```

### 3.3 StateTransitionTable
统计状态迁移次数。

```python
from pyStateView.widgets.state_transition_table import StateTransitionTable
table = StateTransitionTable()
table.update_from_events(flow.model.events)
```

### 3.4 EventLogView（可选）
事件列表，双击定位 PhaseFlow 时间块。

```python
from pyStateView.widgets.event_log_view import EventLogView
log = EventLogView()
log.update_from_events(flow.model.events)
```

## 4. 安装步骤
```bash
pip install .
```

## 5. 工程应用场景
- 风扇工况：随温度/负载变化的状态监控
- 逆变器：电源工况状态机追踪
- SCADA：离散量状态趋势

## 6. 与 pyqtgraph/echarts 区别
- pyqtgraph/echarts 偏向数值曲线与预测插值
- pyStateView 只表达**离散状态事实**，不做曲线、不做平滑

## 7. API 文档（简要）
### PhaseFlow
- `append_event(timestamp, state_id, extra=None)`
- `set_state_order(states)`
- `set_color_map(color_map)`
- `set_time_scale(pixels_per_second)`

### StateIndicator
- `set_state(state_id, blink=False)`

### StateDistributionBar
- `update_from_events(events, start_time=None, end_time=None)`

### StateTransitionTable
- `update_from_events(events)`

### EventLogView
- `update_from_events(events)`
- `locate_event` signal

## 8. 示例
- `examples/fan_state_demo.py`
- `examples/inverter_state_demo.py`
