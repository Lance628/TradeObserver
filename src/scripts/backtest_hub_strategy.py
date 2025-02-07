import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.analyzers.realtime.hub_analyzer import HubAnalyzer
from src.database.database import DatabaseManager
from src.models.candle import Candle

def run_backtest(
    code: str,
    start_date: str,
    end_date: str,
    period: int = 5,
    initial_capital: float = 600000.0,
    params_combinations: List[Dict] = None
) -> List[Dict]:
    """
    运行回测并返回所有参数组合的结果
    
    Args:
        code: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        period: K线周期（分钟）
        initial_capital: 初始资金
        params_combinations: 参数组合列表
    """
    # 如果没有提供参数组合，使用默认的参数生成函数
    if params_combinations is None:
        params_combinations = generate_params_combinations()
    
    # 初始化数据库管理器
    db_manager = DatabaseManager()
    
    # 获取历史数据
    historical_data = db_manager.get_candles(
        code=code,
        period=period,
        limit=100000
    )
    
    if not historical_data:
        print(f"未找到股票 {code} 的历史数据")
        return []
    
    # 计算区间涨跌幅
    first_open = historical_data[0].open
    last_close = historical_data[-1].close
    period_return = (last_close - first_open) / first_open * 100
    
    # 初始化分析器并运行回测
    analyzer = HubAnalyzer(code=code, period=period)
    
    # 初始化结果列表
    all_results = []
    
    # 遍历参数组合进行回测
    for params in params_combinations:
        print(f"当前参数: {params}")
        # 设置中枢形成所需K线数
        min_candles = params.pop('min_candles_for_hub')
        analyzer.min_candles_for_hub = min_candles
        
        result = analyzer.backtest(
            historical_candles=historical_data,
            initial_capital=initial_capital,
            **params
        )
        
        # 把min_candles_for_hub加回参数中
        params['min_candles_for_hub'] = min_candles
        
        # 保存结果和参数
        result['params'] = params.copy()
        result['period_return'] = period_return
        result['code'] = code
        result['period'] = period
        
        all_results.append(result)
    
    # 找出最优结果并打印
    best_result = max(all_results, key=lambda x: x['total_return'])
    print("\n====== 当前股票最优参数组合 ======")
    print(f"股票代码: {code}")
    print(f"K线周期: {period}分钟")
    print(f"区间涨跌幅: {best_result['period_return']:.2f}%")
    print(f"中枢形成K线数: {best_result['params']['min_candles_for_hub']}")
    print(f"追加仓位止盈: {best_result['params']['additional_take_profit']:.2%}")
    print(f"追加仓位止损: {best_result['params']['additional_stop_loss']:.2%}")
    print(f"减仓成功回补: {best_result['params']['reduction_success']:.2%}")
    print(f"减仓失败回补: {best_result['params']['reduction_fail']:.2%}")
    print(f"总收益率: {best_result['total_return']:.2f}%")
    
    return all_results

def find_best_params(all_results: List[Dict]) -> Tuple[Dict, List[Dict]]:
    """
    根据所有股票的回测结果找出最优参数组合
    
    Returns:
        Tuple[Dict, List[Dict]]: (最优参数组合, 该参数组合下各股票的表现列表)
    """
    # 按参数组合对结果进行分组
    params_performance = {}
    
    for result in all_results:
        # 将参数转换为可哈希的元组形式作为键
        params_key = tuple(sorted(result['params'].items()))
        
        # 计算超额收益（相对于区间涨跌幅的绝对差值）
        excess_return = result['total_return'] - result['period_return']
        
        if params_key not in params_performance:
            params_performance[params_key] = {
                'excess_returns': [],
                'params': result['params'],
                'stock_performances': []  # 新增：记录每只股票的表现
            }
        
        params_performance[params_key]['excess_returns'].append(excess_return)
        # 新增：保存股票详细表现
        params_performance[params_key]['stock_performances'].append({
            'code': result['code'],
            'period': result['period'],
            'total_return': result['total_return'],
            'period_return': result['period_return'],
            'excess_return': excess_return
        })
    
    # 计算每个参数组合的平均超额收益
    for perf in params_performance.values():
        perf['avg_excess_return'] = sum(perf['excess_returns']) / len(perf['excess_returns'])
    
    # 找出平均超额收益最大的参数组合
    best_params_data = max(
        params_performance.values(),
        key=lambda x: x['avg_excess_return']
    )
    
    # 打印最优参数下各股票的表现
    print("\n====== 最优参数下各股票表现 ======")
    print(f"平均超额收益: {best_params_data['avg_excess_return']:.2f}%")
    print("\n各股票具体表现:")
    print("股票代码  周期  总收益率    区间涨跌幅  超额收益")
    print("-" * 50)
    
    # 按超额收益排序
    sorted_performances = sorted(
        best_params_data['stock_performances'],
        key=lambda x: x['excess_return'],
        reverse=True
    )
    
    for perf in sorted_performances:
        print(f"{perf['code']}  {perf['period']}分钟  "
              f"{perf['total_return']:8.2f}%  "
              f"{perf['period_return']:8.2f}%  "
              f"{perf['excess_return']:8.2f}%")
    
    return best_params_data['params'], sorted_performances

def plot_trading_results(candles: List[Candle], trades: List[Dict], code: str):
    """绘制交易结果图表"""
    # 准备数据
    dates = [c.timestamp for c in candles]
    prices = [c.close for c in candles]
    
    # 创建图表
    plt.figure(figsize=(15, 8))
    plt.plot(dates, prices, label='价格', color='gray', alpha=0.6)
    
    # 标记买入点和卖出点
    buy_dates = [t['time'] for t in trades if t['type'] == '买入']
    buy_prices = [t['price'] for t in trades if t['type'] == '买入']
    sell_dates = [t['time'] for t in trades if t['type'] == '卖出']
    sell_prices = [t['price'] for t in trades if t['type'] == '卖出']
    
    plt.scatter(buy_dates, buy_prices, color='red', marker='^', s=100, label='买入')
    plt.scatter(sell_dates, sell_prices, color='green', marker='v', s=100, label='卖出')
    
    plt.title(f'{code} 中枢策略回测结果')
    plt.xlabel('时间')
    plt.ylabel('价格')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    
    # 保存图表
    output_dir = 'output/backtest'
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f'{output_dir}/{code}_backtest_result.png', bbox_inches='tight')
    plt.close()

def save_results_to_excel(results: Dict):
    """
    保存回测结果到Excel文件，包含汇总和交易明细
    每个回测结果保存在单独的sheet中，sheet名包含股票代码和周期信息
    """
    output_dir = 'output/backtest'
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_path = f'{output_dir}/backtest_results_{timestamp}.xlsx'
    
    # 创建Excel写入器
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # 创建汇总表
        summary_data = []
        for (code, period), result in results.items():
            if result:  # 确保有结果
                summary_data.append({
                    '股票代码': code,
                    '周期(分钟)': period,
                    '初始资金': result['initial_capital'],
                    '最终市值': result['final_value'],
                    '总收益率': f"{result['total_return']:.2f}%",
                    '最大回撤': f"{result['max_drawdown']:.2f}%",
                    '总交易次数': result['total_trades']
                })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='汇总', index=False)
        
        # 为每个股票创建详细交易sheet
        for (code, period), result in results.items():
            if result and 'trades' in result and result['trades']:
                # 创建sheet名称，包含股票代码和周期信息
                # period = result.get('period', '')
                sheet_name = f'{code}_{period}分钟'
                
                # 准备交易明细数据
                trades_data = []
                position = 0
                cost_basis = 0
                for trade in result['trades']:
                    if trade['type'] == '买入':
                        position += trade['shares']
                        cost_basis += trade['shares'] * trade['price']
                    else:  # 卖出
                        position -= trade['shares']
                        if position == 0:
                            cost_basis = 0
                    
                    trades_data.append({
                        '交易时间': trade['time'],
                        '交易类型': trade['type'],
                        '成交价格': trade['price'],
                        '成交数量': trade['shares'],
                        '成交金额': trade['price'] * trade['shares'],
                        '交易原因': trade.get('reason', ''),
                        '当前持仓': position,
                        # '持仓成本': (cost_basis / position if position > 0 else 0)
                    })
                
                # 创建交易明细DataFrame
                trades_df = pd.DataFrame(trades_data)
                
                # 计算不同类型交易的统计
                position_stats = {
                    'additional': {'success': 0, 'fail': 0, 'profit': 0, 'loss': 0, 'ratios': []},
                    'reduction': {'success': 0, 'fail': 0, 'profit': 0, 'loss': 0, 'ratios': []}
                }

                # 统计所有交易
                for t in result['trades']:
                    if '初始建仓' in t.get('reason', '') or '回测结束清仓' in t.get('reason', ''):
                        continue
                        
                    reason = t.get('reason', '')
                    pnl = t.get('pnl', 0)
                    
                    # 解析交易原因中的比例
                    ratio_str = reason.split()[-1].strip('%')
                    try:
                        ratio = float(ratio_str) / 100
                    except:
                        ratio = 0
                    
                    # 追加仓位统计
                    if '[追加仓位]' in reason:
                        if '[成功]' in reason:
                            position_stats['additional']['success'] += 1
                            position_stats['additional']['profit'] += pnl
                            position_stats['additional']['ratios'].append(ratio)
                        elif '[失败]' in reason:
                            position_stats['additional']['fail'] += 1
                            position_stats['additional']['loss'] += abs(pnl)
                            position_stats['additional']['ratios'].append(ratio)
                    
                    # 减仓统计
                    elif '[减仓]' in reason:
                        if '[成功]' in reason:
                            position_stats['reduction']['success'] += 1
                            position_stats['reduction']['profit'] += pnl
                            position_stats['reduction']['ratios'].append(ratio)
                        elif '[失败]' in reason:
                            position_stats['reduction']['fail'] += 1
                            position_stats['reduction']['loss'] += abs(pnl)
                            position_stats['reduction']['ratios'].append(ratio)

                # 计算平均比例和其他指标
                def calculate_metrics(stats):
                    total = stats['success'] + stats['fail']
                    if total == 0:
                        return "0%", "0%", "∞", "0%"
                    
                    win_rate = f"{(stats['success']/total*100):.2f}%"
                    avg_ratio = f"{(sum(stats['ratios'])/len(stats['ratios'])*100):.2f}%" if stats['ratios'] else "0%"
                    profit_ratio = f"{(stats['profit']/stats['loss']):.2f}" if stats['loss'] > 0 else "∞"
                    total_pnl_ratio = f"{((stats['profit']-stats['loss'])/result['initial_capital']*100):.2f}%"
                    
                    return win_rate, avg_ratio, profit_ratio, total_pnl_ratio

                add_metrics = calculate_metrics(position_stats['additional'])
                red_metrics = calculate_metrics(position_stats['reduction'])

                stats_data = pd.DataFrame([
                    ['股票代码', code],
                    ['K线周期', f"{period}分钟"],
                    ['区间涨跌幅', f"{result['period_return']:.2f}%"],
                    ['参数设置', ''],
                    ['  中枢形成K线数', result['params']['min_candles_for_hub']],
                    ['  追加仓位止盈', f"{result['params']['additional_take_profit']:.2%}"],
                    ['  追加仓位止损', f"{result['params']['additional_stop_loss']:.2%}"],
                    ['  减仓成功回补', f"{result['params']['reduction_success']:.2%}"],
                    ['  减仓失败回补', f"{result['params']['reduction_fail']:.2%}"],
                    ['回测结果', ''],
                    ['  初始资金', f"{result['initial_capital']:,.2f}"],
                    ['  最终市值', f"{result['final_value']:,.2f}"],
                    ['  总收益率', f"{result['total_return']:.2f}%"],
                    ['  最大回撤', f"{result['max_drawdown']:.2f}%"],
                    ['  总交易次数', result['total_trades']],
                    ['追加仓位统计', ''],
                    ['  成功次数', position_stats['additional']['success']],
                    ['  失败次数', position_stats['additional']['fail']],
                    ['  盈利金额', f"{position_stats['additional']['profit']:,.2f}"],
                    ['  亏损金额', f"{position_stats['additional']['loss']:,.2f}"],
                    ['  成功率', add_metrics[0]],
                    ['  平均比例', add_metrics[1]],
                    ['  盈亏比', add_metrics[2]],
                    ['  收益占比', add_metrics[3]],
                    ['减仓统计', ''],
                    ['  成功次数', position_stats['reduction']['success']],
                    ['  失败次数', position_stats['reduction']['fail']],
                    ['  盈利金额', f"{position_stats['reduction']['profit']:,.2f}"],
                    ['  亏损金额', f"{position_stats['reduction']['loss']:,.2f}"],
                    ['  成功率', red_metrics[0]],
                    ['  平均比例', red_metrics[1]],
                    ['  盈亏比', red_metrics[2]],
                    ['  收益占比', red_metrics[3]]
                ], columns=['指标', '数值'])
                
                # 写入Excel，在股票代码sheet中包含统计信息和交易明细
                stats_data.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
                trades_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=len(stats_data) + 2)
        
        print(f"\n回测结果已保存到: {excel_path}")

def generate_params_combinations():
    """生成参数组合"""
    params_combinations = []
    
    # 定义参数范围
    take_profit_range = [i * 0.005 for i in range(2, 8)]  # 0.01 到 0.035
    stop_loss_range = [i * -0.005 for i in range(2, 8)]   # -0.01 到 -0.035
    reduction_success_range = [i * -0.005 for i in range(2, 8)]  # -0.01 到 -0.035
    reduction_fail_range = [i * 0.005 for i in range(2, 8)]      # 0.01 到 0.035
    min_candles_range = [8,9,10,11,12,13]  # 中枢形成所需K线数
    
    # 生成所有可能的组合
    for take_profit in take_profit_range:
        for stop_loss in stop_loss_range:
            # 止损不应大于止盈
            # if abs(stop_loss) > take_profit:
            #     continue
                
            for reduction_success in reduction_success_range:
                for reduction_fail in reduction_fail_range:
                    # 减仓失败阈值不应大于成功阈值的绝对值
                    # if reduction_fail > abs(reduction_success):
                    #     continue
                        
                    for min_candles in min_candles_range:
                        params_combinations.append({
                            'additional_take_profit': take_profit,
                            'additional_stop_loss': stop_loss,
                            'reduction_success': reduction_success,
                            'reduction_fail': reduction_fail,
                            'min_candles_for_hub': min_candles
                        })
    
    return params_combinations

def main():
    """主函数"""
    # 测试参数
    # test_cases = [
    #     {
    #         'code': '588200',  
    #         'start_date': '2023-01-01',
    #         'end_date': '2025-01-28',
    #         'period': 1,
    #         'initial_capital': 600000.0
    #     },
    #     {
    #         'code': '588200',  
    #         'start_date': '2023-01-01',
    #         'end_date': '2025-01-28',
    #         'period': 5,
    #         'initial_capital': 600000.0
    #     },
    #     {
    #         'code': '588200',  
    #         'start_date': '2023-01-01',
    #         'end_date': '2025-01-28',
    #         'period': 15,
    #         'initial_capital': 600000.0
    #     },
    #     {
    #         'code': '588200',  
    #         'start_date': '2023-01-01',
    #         'end_date': '2025-01-28',
    #         'period': 30,
    #         'initial_capital': 600000.0
    #     },
    #     {
    #         'code': '588200',  
    #         'start_date': '2023-01-01',
    #         'end_date': '2025-01-28',
    #         'period': 60,
    #         'initial_capital': 600000.0
    #     },
    #     {
    #         'code': '588200',  
    #         'start_date': '2023-01-01',
    #         'end_date': '2025-01-28',
    #         'period': 120,
    #         'initial_capital': 600000.0
    #     },
    #     {
    #         'code': '588200',  
    #         'start_date': '2023-01-01',
    #         'end_date': '2025-01-28',
    #         'period': 240,
    #         'initial_capital': 600000.0
    #     }
    # ]


    test_cases = [
        {
            'code': '588200',  
            'start_date': '2023-01-01',
            'end_date': '2025-01-28',
            'period': 5,
            'initial_capital': 600000.0
        },
        {
            'code': '510300',  
            'start_date': '2023-01-01',
            'end_date': '2025-01-28',
            'period': 5,
            'initial_capital': 600000.0
        },
        {
            'code': '510500',  
            'start_date': '2023-01-01',
            'end_date': '2025-01-28',
            'period': 5,
            'initial_capital': 600000.0
        },
        {
            'code': '512690',  
            'start_date': '2023-01-01',
            'end_date': '2025-01-28',
            'period': 5,
            'initial_capital': 600000.0
        }
    ]
    
    # 生成参数组合
    params_combinations = generate_params_combinations()
    # params_combinations = [
    #     {
    #         'additional_take_profit': 0.01,
    #         'additional_stop_loss': -0.01,
    #         'reduction_success': -0.01,
    #         'reduction_fail': 0.01,
    #         'min_candles_for_hub': 11
    #     }
    # ]
    print(f"生成了 {len(params_combinations)} 种参数组合")
    
    # 收集所有回测结果
    all_results = []
    for case in test_cases:
        print(f"\n开始测试 {case['code']}...")
        results = run_backtest(
            params_combinations=params_combinations,
            **case
        )
        all_results.extend(results)
    
    # 找出最优参数组合
    best_params, stock_performances = find_best_params(all_results)
    print("\n====== 全局最优参数组合 ======")
    print(f"中枢形成K线数: {best_params['min_candles_for_hub']}")
    print(f"追加仓位止盈: {best_params['additional_take_profit']:.2%}")
    print(f"追加仓位止损: {best_params['additional_stop_loss']:.2%}")
    print(f"减仓成功回补: {best_params['reduction_success']:.2%}")
    print(f"减仓失败回补: {best_params['reduction_fail']:.2%}")
    
    # 保存详细结果到Excel
    # 按股票和周期组织结果
    organized_results = {}
    for result in all_results:
        key = (result['code'], result['period'])
        if key not in organized_results or result['total_return'] > organized_results[key]['total_return']:
            organized_results[key] = result
    
    save_results_to_excel(organized_results)

if __name__ == "__main__":
    main() 