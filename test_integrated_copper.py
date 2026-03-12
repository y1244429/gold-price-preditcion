"""
测试集成后的铜价预测模型
验证四层宏观因子是否正确整合
"""
import sys
sys.path.insert(0, '/Users/ydy/CodeBuddy/20260310193311')

from gold_app import predict_copper_price, get_copper_data
import json

def test_integrated_prediction():
    """测试集成宏观因子的铜价预测"""
    print("=" * 70)
    print("🔶 测试集成四层宏观因子的铜价预测")
    print("=" * 70)
    
    # 获取铜价数据
    df = get_copper_data()
    if df is None:
        print("❌ 无法获取铜价数据")
        return
    
    print(f"\n📊 获取到 {len(df)} 条铜价数据")
    print(f"   当前价格: {df['Close'].iloc[-1]:.2f}")
    
    # 执行预测
    print("\n🔮 执行预测...")
    result = predict_copper_price(df)
    
    # 检查结果
    print("\n" + "=" * 70)
    print("📋 预测结果")
    print("=" * 70)
    
    print(f"当前价格: {result['current_price']:.2f}")
    print(f"7日后预测 (集成): {result['predictions']['Ensemble']:.2f}")
    
    if 'macro_adjustment' in result and result['macro_adjustment']:
        macro = result['macro_adjustment']
        print(f"\n🌍 四层宏观因子调整:")
        print(f"   综合得分: {macro['composite_score']:+.3f}")
        print(f"   交易信号: {macro['signal']}")
        print(f"   调整幅度: {macro['adjustment_pct']:+.1f}%")
        print(f"   置信度: {macro['confidence']:.1%}")
        
        print(f"\n   各层得分:")
        for layer_key, layer in macro['layers'].items():
            print(f"      {layer['name']}: {layer['score']:+.3f} (权重{layer['weight']:.0%})")
    else:
        print("\n⚠️ 宏观因子调整未启用或失败")
    
    if 'risk_metrics' in result:
        print(f"\n🛡️ 风险管理指标已包含")
    
    # 保存结果
    output_file = "/Users/ydy/CodeBuddy/20260310193311/output/copper_integrated_test.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 结果已保存: {output_file}")
    print("=" * 70)
    
    return result

if __name__ == "__main__":
    test_integrated_prediction()
