# 修复中文字体显示问题 Spec

## Why
游戏界面中的所有中文文字显示为方框（□□□），无法正常阅读，严重影响用户体验。

## What Changes
- 修复字体加载逻辑，确保使用支持中文的字体
- 添加字体文件检测和回退机制
- 确保所有场景的文字都能正确显示

## Impact
- Affected specs: 字体系统、UI渲染
- Affected code: gomoku.py (ResourceManager.load_fonts 方法)

## ADDED Requirements

### Requirement: 中文字体自动检测
系统应能够自动检测并加载系统中可用的中文字体。

#### Scenario: 自动选择最佳中文字体
- **WHEN** 游戏启动时
- **THEN** 系统应扫描系统中所有可用字体
- **AND** 优先选择支持中文的字体（如微软雅黑、宋体等）
- **AND** 验证字体是否真的能正确渲染中文

#### Scenario: 字体回退机制
- **WHEN** 无法找到任何中文字体时
- **THEN** 使用系统默认字体作为后备方案
- **AND** 如果默认字体也不支持中文，则下载或使用内嵌的字体资源

## MODIFIED Requirements

### Requirement: 字体加载系统
原有的字体加载逻辑需要完全重写，采用更可靠的字体检测机制：

1. 使用 `pygame.font.match_font()` 进行精确匹配
2. 实际测试字体是否能正确渲染中文
3. 提供多级回退方案
4. 添加调试日志帮助排查问题

### Requirement: UI文字渲染
所有UI组件应确保使用的字体支持中文显示。
