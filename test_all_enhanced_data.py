"""
测试所有增强版数据源
"""
import sys

def test_gpr():
    """测试GPR数据"""
    print("\n" + "=" * 70)
    print("1️⃣  测试 GPR (地缘政治风险)")
    print("=" * 70)
    try:
        from enhanced_gpr_epu import get_gpr_index
        gpr = get_gpr_index()
        
        if gpr.get('value') is not None:
            print(f"✅ GPR数据获取成功!")
            print(f"   当前值: {gpr['value']}")
            print(f"   数据源: {gpr['data_source']}")
            print(f"   可信度: {gpr['reliability']}")
            return True
        else:
            print(f"❌ GPR获取失败: {gpr.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ GPR测试出错: {e}")
        return False

def test_epu():
    """测试EPU数据"""
    print("\n" + "=" * 70)
    print("2️⃣  测试 EPU (经济不确定性)")
    print("=" * 70)
    try:
        from enhanced_gpr_epu import get_epu_index
        
        # 测试中国EPU
        epu_cn = get_epu_index('China')
        if epu_cn.get('value') is not None:
            print(f"✅ EPU-China获取成功!")
            print(f"   当前值: {epu_cn['value']}")
            print(f"   数据源: {epu_cn['data_source']}")
        else:
            print(f"⚠️  EPU-China获取失败: {epu_cn.get('error')}")
        
        # 测试美国EPU
        epu_us = get_epu_index('US')
        if epu_us.get('value') is not None:
            print(f"✅ EPU-US获取成功!")
            print(f"   当前值: {epu_us['value']}")
            print(f"   数据源: {epu_us['data_source']}")
            return True
        else:
            print(f"⚠️  EPU-US获取失败: {epu_us.get('error')}")
            return epu_cn.get('value') is not None
            
    except Exception as e:
        print(f"❌ EPU测试出错: {e}")
        return False

def test_etf():
    """测试ETF持仓数据"""
    print("\n" + "=" * 70)
    print("3️⃣  测试 ETF持仓 (黄金ETF)")
    print("=" * 70)
    try:
        from etf_holdings_collector import get_etf_holdings
        etf = get_etf_holdings(priority='official')
        
        if etf.get('value') is not None:
            print(f"✅ ETF持仓获取成功!")
            print(f"   持仓量: {etf['value']} 吨")
            print(f"   数据源: {etf['data_source']}")
            print(f"   可信度: {etf['reliability']}")
            return True
        else:
            print(f"❌ ETF获取失败: {etf.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ ETF测试出错: {e}")
        return False

def test_integration():
    """测试集成到gold_app"""
    print("\n" + "=" * 70)
    print("4️⃣  测试集成到 MacroFactorCollector")
    print("=" * 70)
    try:
        from gold_app import MacroFactorCollector
        
        collector = MacroFactorCollector()
        
        # 测试GPR
        print("\n   测试 get_gpr()...")
        gpr_data = collector.get_gpr()
        print(f"   GPR: {gpr_data.get('value')} (来源: {gpr_data.get('data_source', 'N/A')[:40]}...)")
        
        # 测试EPU
        print("\n   测试 get_epu()...")
        epu_data = collector.get_epu()
        print(f"   EPU: {epu_data.get('value')} (来源: {epu_data.get('data_source', 'N/A')[:40]}...)")
        
        # 测试ETF
        print("\n   测试 get_etf_holdings()...")
        etf_data = collector.get_etf_holdings()
        print(f"   ETF: {etf_data.get('value')} 吨 (来源: {etf_data.get('data_source', 'N/A')[:40]}...)")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("\n" + "🧪 " * 35)
    print("📊 增强版数据源测试套件")
    print("🧪 " * 35)
    
    results = {
        'GPR': test_gpr(),
        'EPU': test_epu(),
        'ETF': test_etf(),
        'Integration': test_integration()
    }
    
    # 汇总
    print("\n" + "=" * 70)
    print("📋 测试结果汇总")
    print("=" * 70)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {status}: {name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n   总计: {passed}/{total} 通过 ({passed/total*100:.0f}%)")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 所有测试通过! 可以启动主应用:")
        print("   python gold_app.py")
    else:
        print("\n⚠️  部分测试失败，但应用仍可使用备用数据源")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
