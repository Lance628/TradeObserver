import math
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
    if best_result['params']['additional_take_profit'] is not None: 
        print(f"追加仓位止盈: {best_result['params']['additional_take_profit']:.2%}")
    else:
        print("追加仓位止盈: 禁用")
    if best_result['params']['additional_stop_loss'] is not None:
        print(f"追加仓位止损: {best_result['params']['additional_stop_loss']:.2%}")
    else:
        print("追加仓位止损: 禁用")
    if best_result['params']['reduction_success'] is not None:
            print(f"减仓成功回补: {best_result['params']['reduction_success']:.2%}")
    else:
        print("减仓成功回补: 禁用")
    if best_result['params']['reduction_fail'] is not None:
        print(f"减仓失败回补: {best_result['params']['reduction_fail']:.2%}")
    else:
        print("减仓失败回补: 禁用")
    print(f"总收益率: {best_result['total_return']:.2f}%")
    
    # 在返回结果之前，导出所有回测结果到Excel
    output_dir = 'output/backtest'
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_path = f'{output_dir}/{code}_{period}min_all_results_{timestamp}.xlsx'
    
    # 准备数据
    results_data = []
    for result in all_results:
        # 计算交易统计
        successful_trades = sum(1 for t in result['trades'] 
                              if t.get('pnl', 0) > 0 and 
                              '初始建仓' not in t.get('reason', '') and 
                              '回测结束清仓' not in t.get('reason', ''))
        total_trades = math.floor(sum(1 for t in result['trades'] 
                          if '初始建仓' not in t.get('reason', '') and 
                          '回测结束清仓' not in t.get('reason', ''))/2)

        win_rate = successful_trades / total_trades * 100 if total_trades > 0 else 0
        total_profit = sum(t.get('pnl', 0) for t in result['trades'])
        
        results_data.append({
            '股票代码': code,
            '周期(分钟)': period,
            '中枢形成K线数': result['params']['min_candles_for_hub'],
            '追加仓位止盈': f"{result['params']['additional_take_profit']:.2%}" if result['params']['additional_take_profit'] is not None else '禁用',
            '追加仓位止损': f"{result['params']['additional_stop_loss']:.2%}" if result['params']['additional_stop_loss'] is not None else '禁用',
            '减仓成功回补': f"{result['params']['reduction_success']:.2%}" if result['params']['reduction_success'] is not None else '禁用',
            '减仓失败回补': f"{result['params']['reduction_fail']:.2%}" if result['params']['reduction_fail'] is not None else '禁用',
            '总收益率': f"{result['total_return']:.2f}%",
            '区间涨跌幅': f"{result['period_return']:.2f}%",
            '超额收益率': f"{result['total_return'] - result['period_return']:.2f}%",
            '总交易次数': total_trades,
            '成功交易数': successful_trades,
            '胜率': f"{win_rate:.2f}%",
            '收益金额': total_profit,
            '最终金额': result['final_value'],
            '评估分数(收益*胜率)': total_profit * (win_rate/100)
        })
    
    # 创建DataFrame并保存到Excel
    df = pd.DataFrame(results_data)
    
    # 按评估分数降序排序
    df = df.sort_values('评估分数(收益*胜率)', ascending=False)
    
    # 保存到Excel
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # 保存汇总结果
        df.to_excel(writer, sheet_name='参数回测结果', index=False)
        
        # 保存最优参数的详细交易记录
        best_result = max(all_results, key=lambda x: x['total_return'])
        trades_data = []
        position = 0
        for trade in best_result['trades']:
            if trade['type'] == '买入':
                position += trade['shares']
            else:
                position -= trade['shares']
            
            trades_data.append({
                '交易时间': trade['time'],
                '交易类型': trade['type'],
                '成交价格': trade['price'],
                '成交数量': trade['shares'],
                '成交金额': trade['price'] * trade['shares'],
                '交易原因': trade.get('reason', ''),
                '当前持仓': position,
                '收益': trade.get('pnl', 0)
            })
        
        trades_df = pd.DataFrame(trades_data)
        trades_df.to_excel(writer, sheet_name='最优参数交易记录', index=False)
    
    print(f"\n所有回测结果已保存到: {excel_path}")
    
    return all_results

# def find_best_params(all_results: List[Dict]) -> Tuple[Dict, List[Dict]]:
#     """
#     根据所有股票的回测结果找出最优参数组合（基于超额收益率）
#     """
#     # 按参数组合对结果进行分组
#     params_performance = {}
    
#     for result in all_results:
#         # 将参数转换为可哈希的元组形式作为键
#         params_key = tuple(sorted(result['params'].items()))
        
#         # 计算超额收益（相对于区间涨跌幅的绝对差值）
#         excess_return = result['total_return'] - result['period_return']
        
#         if params_key not in params_performance:
#             params_performance[params_key] = {
#                 'excess_returns': [],
#                 'params': result['params'],
#                 'stock_performances': []  # 新增：记录每只股票的表现
#             }
        
#         params_performance[params_key]['excess_returns'].append(excess_return)
#         # 新增：保存股票详细表现
#         params_performance[params_key]['stock_performances'].append({
#             'code': result['code'],
#             'period': result['period'],
#             'total_return': result['total_return'],
#             'period_return': result['period_return'],
#             'excess_return': excess_return
#         })
    
#     # 计算每个参数组合的平均超额收益
#     for perf in params_performance.values():
#         perf['avg_excess_return'] = sum(perf['excess_returns']) / len(perf['excess_returns'])
    
#     # 找出平均超额收益最大的参数组合
#     best_params_data = max(
#         params_performance.values(),
#         key=lambda x: x['avg_excess_return']
#     )
    
#     # 打印最优参数下各股票的表现
#     print("\n====== 最优参数下各股票表现（超额收益率） ======")
#     print(f"平均超额收益: {best_params_data['avg_excess_return']:.2f}%")
#     print("\n各股票具体表现:")
#     print("股票代码  周期  总收益率    区间涨跌幅  超额收益  总交易次数  成功交易  胜率   收益金额")
#     print("-" * 90)
    
#     # 按超额收益排序
#     sorted_performances = sorted(
#         best_params_data['stock_performances'],
#         key=lambda x: x['excess_return'],
#         reverse=True
#     )
#     # TODO: 这里有问题
#     for perf in sorted_performances[:1]:
#         successful_trades = sum(1 for t in result['trades'] 
#                               if t.get('pnl', 0) > 0 and 
#                               '初始建仓' not in t.get('reason', '') and 
#                               '回测结束清仓' not in t.get('reason', ''))
#         total_trades = sum(1 for t in result['trades'] 
#                           if '初始建仓' not in t.get('reason', '') and 
#                           '回测结束清仓' not in t.get('reason', ''))
#         win_rate = successful_trades / total_trades * 100 if total_trades > 0 else 0
#         total_profit = sum(t.get('pnl', 0) for t in result['trades'])
        
#         print(f"{perf['code']}  {perf['period']}分钟  "
#               f"{perf['total_return']:8.2f}%  "
#               f"{perf['period_return']:8.2f}%  "
#               f"{perf['excess_return']:8.2f}%  "
#               f"{total_trades:8d}  "
#               f"{successful_trades:8d}  "
#               f"{win_rate:6.2f}%  "
#               f"{total_profit:10,.2f}")
        
#         # 更新性能数据
#         perf.update({
#             'total_trades': total_trades,
#             'successful_trades': successful_trades,
#             'win_rate': win_rate,
#             'profit_amount': total_profit
#         })
    
#     return best_params_data['params'], sorted_performances

# def find_best_params_by_profit_and_winrate(all_results: List[Dict]) -> Tuple[Dict, List[Dict]]:
#     """
#     根据所有股票的回测结果找出最优参数组合
#     评估指标 = 平均收益金额 * 平均交易成功率
    
#     Returns:
#         Tuple[Dict, List[Dict]]: (最优参数组合, 该参数组合下各股票的表现列表)
#     """
#     # 按参数组合对结果进行分组
#     params_performance = {}
    
#     for result in all_results:
#         params_key = tuple(sorted(result['params'].items()))
        
#         # 计算交易成功率和收益金额
#         successful_trades = 0
#         total_trades = 0
#         total_profit = 0
        
#         for trade in result['trades']:
#             if '初始建仓' in trade.get('reason', '') or '回测结束清仓' in trade.get('reason', ''):
#                 continue
                
#             total_trades += 1
#             pnl = trade.get('pnl', 0)
#             if pnl > 0:
#                 successful_trades += 1
#             total_profit += pnl
        
#         win_rate = successful_trades / (total_trades/2) if total_trades > 0 else 0
#         profit_amount = total_profit
        
#         if params_key not in params_performance:
#             params_performance[params_key] = {
#                 'win_rates': [],
#                 'profit_amounts': [],
#                 'params': result['params'],
#                 'stock_performances': []
#             }
        
#         params_performance[params_key]['win_rates'].append(win_rate)
#         params_performance[params_key]['profit_amounts'].append(profit_amount)
#         params_performance[params_key]['stock_performances'].append({
#             'code': result['code'],
#             'period': result['period'],
#             'total_return': result['total_return'],
#             'period_return': result['period_return'],
#             'win_rate': win_rate * 100,  # 转换为百分比
#             'profit_amount': profit_amount,
#             'total_trades': total_trades,
#             'successful_trades': successful_trades
#         })
    
#     # 计算每个参数组合的平均表现
#     for perf in params_performance.values():
#         perf['avg_win_rate'] = sum(perf['win_rates']) / len(perf['win_rates'])
#         perf['avg_profit_amount'] = sum(perf['profit_amounts']) / len(perf['profit_amounts'])
#         # 评估指标 = 平均收益金额 * 平均胜率
#         perf['score'] = perf['avg_profit_amount'] * perf['avg_win_rate']
    
#     # 找出评估指标最高的参数组合
#     best_params_data = max(
#         params_performance.values(),
#         key=lambda x: x['score']
#     )
    
#     # 打印最优参数下各股票的表现
#     print("\n====== 最优参数下各股票表现（收益金额*胜率） ======")
#     print(f"平均胜率: {best_params_data['avg_win_rate']*100:.2f}%")
#     print(f"平均收益金额: {best_params_data['avg_profit_amount']:,.2f}")
#     print(f"综合评分: {best_params_data['score']:,.2f}")
#     print("\n各股票具体表现:")
#     print("股票代码  周期  总收益率    区间涨跌幅  超额收益  胜率   收益金额    总交易次数  成功交易")
#     print("-" * 90)
    
#     # 按评估指标（收益金额*胜率）排序
#     sorted_performances = sorted(
#         best_params_data['stock_performances'],
#         key=lambda x: x['profit_amount'] * (x['win_rate']/100),
#         reverse=True
#     )
    
#     for perf in sorted_performances:
#         # 计算超额收益
#         excess_return = perf['total_return'] - perf['period_return']
        
#         print(f"{perf['code']}  {perf['period']}分钟  "
#               f"{perf['total_return']:8.2f}%  "
#               f"{perf['period_return']:8.2f}%  "
#               f"{excess_return:8.2f}%  "
#               f"{perf['win_rate']:6.2f}%  "
#               f"{perf['profit_amount']:10,.2f}  "
#               f"{perf['total_trades']:8d}  "
#               f"{perf['successful_trades']:8d}")
        
#         # 更新性能数据，添加超额收益
#         perf['excess_return'] = excess_return
    
#     return best_params_data['params'], sorted_performances

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

def save_results_to_excel(method1_results: Dict, method2_results: Dict):
    """
    保存回测结果到Excel文件
    
    Args:
        method1_results: 方法一（超额收益率）的结果，包含：
            - params: 最优参数
            - performances: 各股票表现
            - trades: 各股票的交易记录 {(code, period): trades_list}
        method2_results: 方法二（收益金额*胜率）的结果，结构同上
    """
    output_dir = 'output/backtest'
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_path = f'{output_dir}/backtest_results_{timestamp}.xlsx'
    
    # 创建Excel写入器
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # 创建汇总表
        summary_data = []
        for perf in method1_results['performances']:
            method2_perf = next(p for p in method2_results['performances'] 
                              if p['code'] == perf['code'] and p['period'] == perf['period'])
            summary_data.append({
                '股票代码': perf['code'],
                '周期(分钟)': perf['period'],
                '方法一总收益率': f"{perf['total_return']:.2f}%",
                '方法一超额收益': f"{perf['excess_return']:.2f}%",
                '方法一胜率': f"{perf['win_rate']:.2f}%",
                '方法一收益金额': f"{perf['profit_amount']:,.2f}",
                '方法一总交易': perf['total_trades'],
                '方法一成功交易': perf['successful_trades'],
                '方法二总收益率': f"{method2_perf['total_return']:.2f}%",
                '方法二超额收益': f"{method2_perf['excess_return']:.2f}%",
                '方法二胜率': f"{method2_perf['win_rate']:.2f}%",
                '方法二收益金额': f"{method2_perf['profit_amount']:,.2f}",
                '方法二总交易': method2_perf['total_trades'],
                '方法二成功交易': method2_perf['successful_trades'],
                '区间涨跌幅': f"{perf['period_return']:.2f}%"
            })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='汇总', index=False)
        
        # 保存方法一的结果
        # 先创建参数部分的DataFrame
        params_df = pd.DataFrame([
            ['超额收益率优化方法最优参数', '', '', '', '', '', '', '', ''],
            ['中枢形成K线数', method1_results['params']['min_candles_for_hub'], '', '', '', '', '', '', ''],
            ['追加仓位止盈', f"{method1_results['params']['additional_take_profit']:.2%}" if method1_results['params']['additional_take_profit'] is not None else '禁用', '', '', '', '', '', '', ''],
            ['追加仓位止损', f"{method1_results['params']['additional_stop_loss']:.2%}" if method1_results['params']['additional_stop_loss'] is not None else '禁用', '', '', '', '', '', '', ''],
            ['减仓成功回补', f"{method1_results['params']['reduction_success']:.2%}" if method1_results['params']['reduction_success'] is not None else '禁用', '', '', '', '', '', '', ''],
            ['减仓失败回补', f"{method1_results['params']['reduction_fail']:.2%}" if method1_results['params']['reduction_fail'] is not None else '禁用', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', ''],
            ['各股票表现', '', '', '', '', '', '', '', '']
        ], columns=['股票代码', '周期(分钟)', '总收益率', '区间涨跌幅', '超额收益', '胜率', '收益金额', '总交易次数', '成功交易'])
        
        # 创建性能数据的DataFrame
        perf_data = []
        for perf in method1_results['performances']:
            perf_data.append({
                '股票代码': perf['code'],
                '周期(分钟)': perf['period'],
                '总收益率': f"{perf['total_return']:.2f}%",
                '区间涨跌幅': f"{perf['period_return']:.2f}%",
                '超额收益': f"{perf['excess_return']:.2f}%",
                '胜率': f"{perf['win_rate']:.2f}%",
                '收益金额': f"{perf['profit_amount']:,.2f}",
                '总交易次数': perf['total_trades'],
                '成功交易': perf['successful_trades']
            })
        
        perf_df = pd.DataFrame(perf_data)
        method1_df = pd.concat([params_df, perf_df], ignore_index=True)
        method1_df.to_excel(writer, sheet_name='方法一最优结果', index=False)
        
        # 保存方法二的结果（类似方法一）
        params_df = pd.DataFrame([
            ['收益金额*胜率优化方法最优参数', '', '', '', '', '', '', '', ''],
            ['中枢形成K线数', method2_results['params']['min_candles_for_hub'], '', '', '', '', '', '', ''],
            ['追加仓位止盈', f"{method2_results['params']['additional_take_profit']:.2%}" if method2_results['params']['additional_take_profit'] is not None else '禁用', '', '', '', '', '', '', ''],
            ['追加仓位止损', f"{method2_results['params']['additional_stop_loss']:.2%}" if method2_results['params']['additional_stop_loss'] is not None else '禁用', '', '', '', '', '', '', ''],
            ['减仓成功回补', f"{method2_results['params']['reduction_success']:.2%}" if method2_results['params']['reduction_success'] is not None else '禁用', '', '', '', '', '', '', ''],
            ['减仓失败回补', f"{method2_results['params']['reduction_fail']:.2%}" if method2_results['params']['reduction_fail'] is not None else '禁用', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', ''],
            ['各股票表现', '', '', '', '', '', '', '', '']
        ], columns=['股票代码', '周期(分钟)', '总收益率', '区间涨跌幅','超额收益', '胜率', '收益金额', '总交易次数', '成功交易'])
        
        perf_data = []
        for perf in method2_results['performances']:
            perf_data.append({
                '股票代码': perf['code'],
                '周期(分钟)': perf['period'],
                '总收益率': f"{perf['total_return']:.2f}%",
                '区间涨跌幅': f"{perf['period_return']:.2f}%",
                '超额收益': f"{perf['excess_return']:.2f}%",
                '胜率': f"{perf['win_rate']:.2f}%",
                '收益金额': f"{perf['profit_amount']:,.2f}",
                '总交易次数': perf['total_trades'],
                '成功交易': perf['successful_trades']
            })
        
        perf_df = pd.DataFrame(perf_data)
        method2_df = pd.concat([params_df, perf_df], ignore_index=True)
        method2_df.to_excel(writer, sheet_name='方法二最优结果', index=False)
        
        # 为每个方法的每个股票创建详细交易sheet
        for method_name, results in [('方法一', method1_results), ('方法二', method2_results)]:
            for (code, period), trades in results['trades'].items():
                if trades:
                    sheet_name = f'{method_name}_{code}_{period}分钟'
                    trades_data = []
                    position = 0
                    for trade in trades:
                        if trade['type'] == '买入':
                            position += trade['shares']
                        else:
                            position -= trade['shares']
                        
                        trades_data.append({
                            '交易时间': trade['time'],
                            '交易类型': trade['type'],
                            '成交价格': trade['price'],
                            '成交数量': trade['shares'],
                            '成交金额': trade['price'] * trade['shares'],
                            '交易原因': trade.get('reason', ''),
                            '当前持仓': position
                        })
                    
                    trades_df = pd.DataFrame(trades_data)
                    trades_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"\n回测结果已保存到: {excel_path}")

def generate_params_combinations():
    """生成参数组合"""
    params_combinations = []
    
    # 定义参数范围
    take_profit_range = [i * 0.002 for i in range(2, 8)]  # 0.01 到 0.035
    stop_loss_range = [i * -0.002 for i in range(2, 8)]   # -0.01 到 -0.035
    reduction_success_range = [i * -0.002 for i in range(2, 8)]  # -0.01 到 -0.035
    # reduction_success_range = [None]
    reduction_fail_range = [i * 0.002 for i in range(2, 8)]      # 0.01 到 0.035
    # reduction_fail_range = [None]
    min_candles_range = [4,5,6,7,8,9,10,11,12]  # 中枢形成所需K线数
    
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
            'code': '513130',  
            'start_date': '2023-01-01',
            'end_date': '2025-01-28',
            'period': 1,
            'initial_capital': 200000.0
        },
        {
            'code': '513130',  
            'start_date': '2023-01-01',
            'end_date': '2025-01-28',
            'period': 5,
            'initial_capital': 200000.0
        },
        {
            'code': '588200',  
            'start_date': '2023-01-01',
            'end_date': '2025-01-28',
            'period': 1,
            'initial_capital': 200000.0
        },
        {
            'code': '588200',  
            'start_date': '2023-01-01',
            'end_date': '2025-01-28',
            'period': 5,
            'initial_capital': 200000.0
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
    
    # # 找出最优参数组合（两种方法）
    # print("\n====== 方法一：超额收益率优化 ======")
    # best_params_1, stock_performances_1 = find_best_params(all_results)
    
    # print("\n====== 方法二：收益金额*胜率优化 ======")
    # best_params_2, stock_performances_2 = find_best_params_by_profit_and_winrate(all_results)
    
    # print("\n====== 两种方法对比 ======")
    # print("方法一（超额收益率）最优参数：")
    # print(f"中枢形成K线数: {best_params_1['min_candles_for_hub']}")
    # if best_params_1['additional_take_profit'] is not None:
    #     print(f"追加仓位止盈: {best_params_1['additional_take_profit']:.2%}")
    # if best_params_1['additional_stop_loss'] is not None:
    #     print(f"追加仓位止损: {best_params_1['additional_stop_loss']:.2%}")
    # if best_params_1['reduction_success'] is not None:
    #     print(f"减仓成功回补: {best_params_1['reduction_success']:.2%}")
    # if best_params_1['reduction_fail'] is not None:
    #     print(f"减仓失败回补: {best_params_1['reduction_fail']:.2%}")
    
    # print("\n方法二（收益金额*胜率）最优参数：")
    # print(f"中枢形成K线数: {best_params_2['min_candles_for_hub']}")
    # if best_params_2['additional_take_profit'] is not None:
    #     print(f"追加仓位止盈: {best_params_2['additional_take_profit']:.2%}")
    # if best_params_2['additional_stop_loss'] is not None:
    #     print(f"追加仓位止损: {best_params_2['additional_stop_loss']:.2%}")
    # if best_params_2['reduction_success'] is not None:
    #     print(f"减仓成功回补: {best_params_2['reduction_success']:.2%}")
    # if best_params_2['reduction_fail'] is not None:
    #     print(f"减仓失败回补: {best_params_2['reduction_fail']:.2%}")
    
    # # 准备两种方法的结果，包含交易记录
    # method1_results = {
    #     'params': best_params_1,
    #     'performances': stock_performances_1,
    #     'trades': {(perf['code'], perf['period']): result['trades'] 
    #               for result in all_results 
    #               for perf in stock_performances_1 
    #               if (result['code'] == perf['code'] and 
    #                   result['period'] == perf['period'] and 
    #                   result['params'] == best_params_1)}
    # }
    
    # method2_results = {
    #     'params': best_params_2,
    #     'performances': stock_performances_2,
    #     'trades': {(perf['code'], perf['period']): result['trades'] 
    #               for result in all_results 
    #               for perf in stock_performances_2 
    #               if (result['code'] == perf['code'] and 
    #                   result['period'] == perf['period'] and 
    #                   result['params'] == best_params_2)}
    # }
    
    # save_results_to_excel(method1_results, method2_results)

if __name__ == "__main__":
    main() 