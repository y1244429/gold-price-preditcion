"""
测试增强铜价预测 API
"""
import requests
import json

print("=" * 70)
print("🔶 测试增强铜价预测 API")
print("=" * 70)

try:
    response = requests.get('http://127.0.0.1:5001/api/copper-prediction', timeout=30)
    data = response.json()
    
    print(f"\n📊 当前价格: {data['current_price']:,.2f} 元/吨")
    print(f"📈 基础预测 (Ensemble): {data['predictions']['Ensemble']:,.2f} 元/吨")
    
    if 'enhanced_prediction' in data:
        enhanced = data['enhanced_prediction']
        print(f"\n🚀 {enhanced['name']}")
        print(f"   {enhanced['description']}")
        print(f"\n   📊 预测对比:")
        print(f"      原始技术预测: {enhanced['comparison']['原始技术预测']:,.2f} 元/吨")
        print(f"      宏观调整后: {enhanced['comparison']['宏观调整后']:,.2f} 元/吨")
        print(f"      调整幅度: {enhanced['comparison']['调整幅度']}")
        print(f"      调整方向: {enhanced['comparison']['调整方向']}")
        print(f"\n   📈 预测变化: {enhanced['predicted_change_pct']:+.2f}%")
        print(f"   🎯 交易信号: {enhanced['signal']}")
        print(f"   📊 综合得分: {enhanced['composite_score']:+.3f}")
        print(f"   🔒 置信度: {enhanced['confidence']:.1%}")
    
    if 'macro_adjustment' in data:
        macro = data['macro_adjustment']
        print(f"\n🌍 四层宏观因子详情:")
        for layer_key, layer in macro['layers'].items():
            print(f"\n   【{layer['name']}】权重{layer['weight']:.0%} | 得分{layer['score']:+.3f}")
            for factor in layer['factors'][:2]:  # 只显示前2个因子
                direction = "📈" if factor['direction'] == 'BULLISH' else "📉" if factor['direction'] == 'BEARISH' else "➡️"
                print(f"      {direction} {factor['name']}: {factor['score']:+.3f} ({factor['description'][:50]}...)")
    
    # 保存完整结果
    with open('/Users/ydy/CodeBuddy/20260310193311/output/enhanced_copper_api_result.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 完整结果已保存到 output/enhanced_copper_api_result.json")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
