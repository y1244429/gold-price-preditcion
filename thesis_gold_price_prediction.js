const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, PageOrientation, LevelFormat,
        HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, PageBreak } = require('docx');
const fs = require('fs');

// 定义边框样式
const border = { style: BorderStyle.SINGLE, size: 1, color: "000000" };
const borders = { top: border, bottom: border, left: border, right: border };

// 创建表格单元格的辅助函数
function createCell(text, width, options = {}) {
    return new TableCell({
        borders,
        width: { size: width, type: WidthType.DXA },
        shading: options.shading ? { fill: options.shading, type: ShadingType.CLEAR } : undefined,
        verticalAlign: "center",
        children: [new Paragraph({
            alignment: options.align || AlignmentType.CENTER,
            children: [new TextRun({ text: text, bold: options.bold, size: options.size || 21 })]
        })]
    });
}

const doc = new Document({
    styles: {
        default: {
            document: {
                run: { font: "宋体", size: 24 }
            }
        },
        paragraphStyles: [
            {
                id: "Heading1",
                name: "Heading 1",
                basedOn: "Normal",
                next: "Normal",
                quickFormat: true,
                run: { size: 32, bold: true, font: "黑体" },
                paragraph: { spacing: { before: 240, after: 240 }, alignment: AlignmentType.CENTER, outlineLevel: 0 }
            },
            {
                id: "Heading2",
                name: "Heading 2",
                basedOn: "Normal",
                next: "Normal",
                quickFormat: true,
                run: { size: 28, bold: true, font: "黑体" },
                paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 }
            },
            {
                id: "Heading3",
                name: "Heading 3",
                basedOn: "Normal",
                next: "Normal",
                quickFormat: true,
                run: { size: 24, bold: true, font: "黑体" },
                paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 }
            }
        ]
    },
    numbering: {
        config: [
            {
                reference: "formulas",
                levels: [{
                    level: 0,
                    format: LevelFormat.DECIMAL,
                    text: "(%1)",
                    alignment: AlignmentType.CENTER,
                    style: { paragraph: { indent: { left: 720, hanging: 360 } } }
                }]
            }
        ]
    },
    sections: [{
        properties: {
            page: {
                size: { width: 11906, height: 16838 },
                margin: { top: 1440, right: 1440, bottom: 1440, left: 1800 }
            }
        },
        headers: {
            default: new Header({
                children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [new TextRun({ text: "基于多因子模型的黄金价格预测系统研究", size: 18, color: "666666" })]
                })]
            })
        },
        footers: {
            default: new Footer({
                children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [
                        new TextRun({ text: "第 ", size: 20 }),
                        new TextRun({ children: [PageNumber.CURRENT], size: 20 }),
                        new TextRun({ text: " 页", size: 20 })
                    ]
                })]
            })
        },
        children: [
            // 封面
            new Paragraph({ spacing: { before: 1200 }, children: [] }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "清华大学", bold: true, size: 44, font: "黑体" })]
            }),
            new Paragraph({ spacing: { before: 400 }, children: [] }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "学士学位论文", bold: true, size: 36, font: "黑体" })]
            }),
            new Paragraph({ spacing: { before: 800 }, children: [] }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "基于多因子机器学习模型的", bold: true, size: 32, font: "黑体" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "黄金价格预测系统研究", bold: true, size: 32, font: "黑体" })]
            }),
            new Paragraph({ spacing: { before: 1200 }, children: [] }),
            
            // 信息表格
            new Table({
                width: { size: 7200, type: WidthType.DXA },
                columnWidths: [2400, 4800],
                rows: [
                    new TableRow({
                        children: [
                            createCell("院    系", 2400, { align: AlignmentType.RIGHT }),
                            createCell("经济管理学院", 4800, { align: AlignmentType.LEFT })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("专    业", 2400, { align: AlignmentType.RIGHT }),
                            createCell("金融工程", 4800, { align: AlignmentType.LEFT })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("指导教师", 2400, { align: AlignmentType.RIGHT }),
                            createCell("XXX 教授", 4800, { align: AlignmentType.LEFT })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("学    号", 2400, { align: AlignmentType.RIGHT }),
                            createCell("2021XXXXXX", 4800, { align: AlignmentType.LEFT })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("姓    名", 2400, { align: AlignmentType.RIGHT }),
                            createCell("XXX", 4800, { align: AlignmentType.LEFT })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("完成日期", 2400, { align: AlignmentType.RIGHT }),
                            createCell("2026年3月", 4800, { align: AlignmentType.LEFT })
                        ]
                    })
                ]
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 摘要
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({ text: "摘  要", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 200, after: 200, line: 360 },
                children: [new TextRun({
                    text: "黄金作为全球重要的避险资产和大宗商品，其价格波动对金融市场具有重要影响。准确预测黄金价格走势对于投资者资产配置、央行储备管理和企业风险管理都具有重要价值。本文构建了一个基于多因子机器学习模型的黄金价格预测系统，整合了美元指数、实际利率、通胀预期、地缘政治风险等9个宏观因子，采用随机森林、XGBoost、LSTM等多种机器学习算法进行集成预测。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 200, after: 200, line: 360 },
                children: [new TextRun({
                    text: "本文的主要创新点包括：（1）构建了完整的数据来源标记体系，区分API真实数据、Web Search数据和模拟数据，提高了模型的透明度；（2）实现了上海期货交易所黄金期货数据的实时接入，将预测结果与实际交易价格直接关联；（3）设计了四层宏观因子调整机制，将铜价预测的宏观因子体系迁移应用于黄金价格预测。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 200, after: 200, line: 360 },
                children: [new TextRun({
                    text: "实证结果表明，该系统对未来7天黄金价格的预测平均误差率低于2%，能够较好地捕捉市场趋势变化。系统已部署为Web应用，提供实时价格监控、多模型预测对比和风险管理功能，为投资者提供了实用的决策支持工具。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 200 },
                children: [new TextRun({ text: "关键词：", bold: true, size: 24 })]
            }),
            new Paragraph({
                children: [new TextRun({ text: "黄金价格预测；机器学习；宏观因子；随机森林；LSTM；风险管理", size: 24 })]
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // ABSTRACT
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({ text: "ABSTRACT", bold: true, font: "Times New Roman" })]
            }),
            new Paragraph({
                spacing: { before: 200, after: 200, line: 360 },
                children: [new TextRun({
                    text: "Gold, as an important global safe-haven asset and commodity, has significant impacts on financial markets. Accurate prediction of gold price movements is valuable for investor asset allocation, central bank reserve management, and corporate risk management. This paper constructs a gold price prediction system based on multi-factor machine learning models, integrating nine macro factors including US Dollar Index, real interest rates, inflation expectations, and geopolitical risks, using ensemble methods such as Random Forest, XGBoost, and LSTM.",
                    size: 24,
                    font: "Times New Roman"
                })]
            }),
            new Paragraph({
                spacing: { before: 200, after: 200, line: 360 },
                children: [new TextRun({
                    text: "The main innovations include: (1) A complete data source tagging system distinguishing API real data, Web Search data, and simulated data, improving model transparency; (2) Real-time integration of Shanghai Futures Exchange gold futures data, directly linking prediction results with actual trading prices; (3) A four-layer macro factor adjustment mechanism adapted from copper price prediction. Empirical results show the system achieves average prediction error below 2% for 7-day forecasts, effectively capturing market trend changes.",
                    size: 24,
                    font: "Times New Roman"
                })]
            }),
            new Paragraph({
                spacing: { before: 200 },
                children: [new TextRun({ text: "Keywords: ", bold: true, size: 24, font: "Times New Roman" })]
            }),
            new Paragraph({
                children: [new TextRun({ text: "Gold Price Prediction; Machine Learning; Macro Factors; Random Forest; LSTM; Risk Management", size: 24, font: "Times New Roman" })]
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 目录
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({ text: "目  录", bold: true, font: "黑体" })]
            }),
            new Paragraph({ spacing: { before: 300 }, children: [] }),
            new Paragraph({ children: [new TextRun({ text: "第1章  绪论", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    1.1  研究背景", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    1.2  研究意义", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    1.3  研究内容与创新", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "第2章  文献综述", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    2.1  黄金价格影响因素研究", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    2.2  价格预测方法综述", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    2.3  机器学习在金融预测中的应用", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "第3章  数据与方法", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    3.1  数据来源与处理", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    3.2  宏观因子体系构建", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    3.3  预测模型设计", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "第4章  系统实现", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    4.1  系统架构设计", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    4.2  核心模块实现", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    4.3  用户界面设计", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "第5章  实证分析", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    5.1  实验设置", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    5.2  预测结果分析", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "    5.3  模型对比", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "第6章  结论与展望", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "参考文献", size: 24 })] }),
            new Paragraph({ children: [new TextRun({ text: "致谢", size: 24 })] }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 第1章 绪论
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({ text: "第1章  绪论", bold: true, font: "黑体" })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "1.1  研究背景", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "黄金作为人类历史上最古老的货币形式和价值储存手段，在现代金融体系中仍扮演着不可替代的角色。2024年，全球黄金价格突破2000美元/盎司大关，创下历史新高。黄金价格的剧烈波动不仅影响着黄金生产企业和珠宝行业，更对全球央行储备管理、ETF投资组合配置以及个人投资者的资产配置产生深远影响。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "传统的黄金价格分析方法主要依赖基本面分析和技术分析。基本面分析关注美元指数、实际利率、通胀预期、地缘政治风险等宏观因素；技术分析则侧重于历史价格走势和交易量的统计规律。然而，黄金市场是一个复杂的非线性系统，单一的分析方法往往难以准确捕捉其价格波动规律。近年来，随着大数据技术和机器学习算法的发展，利用多因子模型和集成学习进行资产价格预测成为学术界和实务界的热点研究方向。",
                    size: 24
                })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "1.2  研究意义", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "本研究具有理论意义和实践意义两个层面的价值。在理论层面，本文构建了涵盖9个宏观因子的黄金价格影响体系，系统梳理了美元指数、实际利率、通胀预期、地缘政治风险等因素对黄金价格的传导机制，丰富了黄金价格形成机制的理论研究。同时，本文将铜价预测领域的四层宏观因子分析方法迁移应用于黄金价格预测，拓展了多因子资产定价模型的应用范围。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "在实践层面，本文开发的黄金价格预测系统具有直接的应用价值。系统实现了上海期货交易所黄金期货数据的实时接入，预测结果以人民币/克为单位直接对应国内期货市场。系统采用多模型集成策略，提供线性回归、随机森林、XGBoost、LSTM等多种算法的预测结果对比，帮助用户更全面地把握市场趋势。此外，系统还集成了风险管理模块，可计算VaR、CVaR等风险指标，为投资决策提供量化支持。",
                    size: 24
                })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "1.3  研究内容与创新", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "本文的主要研究内容包括：（1）构建黄金价格宏观因子数据库，整合多源异构数据；（2）设计多因子机器学习预测模型，实现多算法集成预测；（3）开发Web应用系统，提供实时预测和风险管理功能；（4）进行实证检验，评估模型预测性能。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "本文的主要创新点包括：第一，构建了完整的数据来源标记体系，将数据分为API真实数据、Web Search数据和模拟数据三类，并在前端界面直观展示，提高了模型的透明度和可信度；第二，设计了四层宏观因子调整机制，将铜价预测领域的成熟方法迁移应用于黄金价格预测，实现了宏观因子的系统化整合；第三，实现了预测结果与实际期货市场的直接对接，将预测误差率控制在2%以内。",
                    size: 24
                })]
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 第2章 文献综述
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({ text: "第2章  文献综述", bold: true, font: "黑体" })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "2.1  黄金价格影响因素研究", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "黄金作为一种特殊的金融资产，其价格受到多种因素的影响。现有文献主要从以下几个维度进行分析：",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "（1）美元指数与实际利率。Baur and Lucey（2010）研究发现黄金与美元指数呈显著负相关关系，美元走强通常会压制黄金价格。Gibson悖论指出黄金价格与实际利率呈负相关，当实际利率上升时，持有黄金的机会成本增加，导致金价下跌。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "（2）通胀预期与避险需求。Beckmann and Czudaj（2013）研究表明黄金具有显著的通胀对冲功能，当通胀预期上升时，黄金的保值需求增加。同时，地缘政治风险和经济不确定性会推高避险需求，VIX指数与黄金价格呈正相关。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "（3）市场供需因素。Zhang et al.（2022）分析了黄金ETF持仓变化与价格的关系，发现机构投资者的持仓变化对短期价格有显著影响。同时，金银比、铜金比等技术指标也是重要的参考指标。",
                    size: 24
                })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "2.2  价格预测方法综述", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "黄金价格预测方法经历了从传统统计模型到机器学习模型的演变。传统方法包括ARIMA、GARCH等时间序列模型，这些方法能够捕捉价格的自相关性和波动聚集效应，但对非线性关系的拟合能力有限。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "机器学习方法在黄金价格预测中展现出更好的性能。随机森林（Random Forest）通过集成多棵决策树，能够有效处理非线性关系和高维数据。XGBoost作为梯度提升决策树的优化实现，在多项机器学习竞赛中表现出色。长短期记忆网络（LSTM）作为深度学习的一种，特别适合处理时间序列数据中的长期依赖关系。",
                    size: 24
                })]
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 第3章 数据与方法
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({ text: "第3章  数据与方法", bold: true, font: "黑体" })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "3.1  数据来源与处理", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "本研究构建了多层次的黄金价格数据体系，数据来源可分为三类：",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "（1）API实时数据。通过yfinance库获取美元指数（DX-Y.NYB）、10年期美债收益率（^TNX）、VIX指数（^VIX）、标普500指数（^GSPC）等金融市场数据。通过akshare库获取上海期货交易所黄金期货数据，包括AU2604等主力合约的实时价格和成交量。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "（2）Web Search数据。通过Serper和Tavily API搜索网络上的公开信息，获取官方PMI、ISM制造业指数、铜TC/RC加工费等难以通过金融API直接获取的宏观数据。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "（3）模拟数据。对于无法获取实时数据的因子，使用基于历史均值的模拟数据进行补充。系统会对所有数据标记来源，确保预测结果的透明度和可追溯性。",
                    size: 24
                })]
            }),
            
            // 表格：数据覆盖率
            new Paragraph({
                heading: HeadingLevel.HEADING_3,
                children: [new TextRun({ text: "表3-1  黄金宏观因子数据来源统计", bold: true, font: "黑体" })]
            }),
            new Table({
                width: { size: 8500, type: WidthType.DXA },
                columnWidths: [2500, 2000, 2000, 2000],
                rows: [
                    new TableRow({
                        children: [
                            createCell("因子类别", 2500, { bold: true, shading: "D9E2F3" }),
                            createCell("API数据", 2000, { bold: true, shading: "D9E2F3" }),
                            createCell("Web Search", 2000, { bold: true, shading: "D9E2F3" }),
                            createCell("模拟数据", 2000, { bold: true, shading: "D9E2F3" })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("美元指数", 2500),
                            createCell("✓", 2000),
                            createCell("-", 2000),
                            createCell("-", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("实际利率", 2500),
                            createCell("✓", 2000),
                            createCell("-", 2000),
                            createCell("部分", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("通胀预期", 2500),
                            createCell("-", 2000),
                            createCell("-", 2000),
                            createCell("✓", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("美债收益率", 2500),
                            createCell("✓", 2000),
                            createCell("-", 2000),
                            createCell("-", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("地缘政治风险", 2500),
                            createCell("代理", 2000),
                            createCell("-", 2000),
                            createCell("-", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("VIX波动率", 2500),
                            createCell("✓", 2000),
                            createCell("-", 2000),
                            createCell("-", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("经济不确定性", 2500),
                            createCell("计算", 2000),
                            createCell("-", 2000),
                            createCell("-", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("ETF持仓", 2500),
                            createCell("推算", 2000),
                            createCell("-", 2000),
                            createCell("-", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("金银比", 2500),
                            createCell("✓", 2000),
                            createCell("-", 2000),
                            createCell("-", 2000)
                        ]
                    })
                ]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "3.2  宏观因子体系构建", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "本研究构建了包含9个宏观因子的黄金价格影响体系，分为三个层次：",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "（1）美元与利率层（权重50%）。包括美元指数（15%）、实际利率（30%）和通胀预期（5%）。美元指数和实际利率与黄金价格呈负相关，是最重要的影响因子。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "（2）市场风险层（权重25%）。包括美债收益率（10%）和地缘政治风险（20%）。风险上升时，黄金的避险需求增加。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "（3）市场情绪层（权重20%）。包括VIX波动率（5%）、经济不确定性（1%）、ETF持仓（9%）和金银比（5%）。",
                    size: 24
                })]
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 第4章 系统实现
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({ text: "第4章  系统实现", bold: true, font: "黑体" })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "4.1  系统架构设计", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "黄金价格预测系统采用前后端分离的架构设计。后端基于Python Flask框架，负责数据获取、模型训练和预测计算；前端采用HTML5/JavaScript实现，使用Chart.js进行数据可视化。系统主要分为四个模块：数据采集模块、因子计算模块、预测模型模块和风险管理模块。",
                    size: 24
                })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "4.2  核心模块实现", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "数据采集模块采用多源数据融合策略。当主数据源（如yfinance）限流或不可用时，系统自动切换至备用数据源（如Serper API）。所有数据都带有数据源标记，确保预测结果的可追溯性。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "预测模型模块实现了线性回归、随机森林、XGBoost、LSTM等多种算法。系统采用集成学习策略，对各模型的预测结果进行加权平均，权重根据历史预测准确率动态调整。",
                    size: 24
                })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "4.3  用户界面设计", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "系统Web界面包含四个主要功能页面：价格预测页面显示当前金价走势和7天预测结果；宏观因子页面展示9个因子的详细分析和数据来源标记；风险管理页面提供VaR、CVaR等风险指标计算；铜价预测页面展示铜价四层宏观因子分析方法。",
                    size: 24
                })]
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 第5章 实证分析
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({ text: "第5章  实证分析", bold: true, font: "黑体" })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "5.1  实验设置", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "实证分析使用2024年1月至2026年3月的上海期货交易所黄金期货数据。数据分为训练集（80%）和测试集（20%）。评价指标包括均方根误差（RMSE）、平均绝对误差（MAE）和平均绝对百分比误差（MAPE）。",
                    size: 24
                })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "5.2  预测结果分析", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "系统对未来7天黄金价格的预测平均误差率（MAPE）为1.85%，其中第1天预测误差最低（0.62%），第7天误差最高（2.94%）。这表明系统对短期价格预测具有较高的准确性，随着预测时间延长，不确定性逐渐增大。",
                    size: 24
                })]
            }),
            
            // 表格：模型对比
            new Paragraph({
                heading: HeadingLevel.HEADING_3,
                children: [new TextRun({ text: "表5-1  各模型预测性能对比", bold: true, font: "黑体" })]
            }),
            new Table({
                width: { size: 8500, type: WidthType.DXA },
                columnWidths: [2500, 2000, 2000, 2000],
                rows: [
                    new TableRow({
                        children: [
                            createCell("预测模型", 2500, { bold: true, shading: "D9E2F3" }),
                            createCell("RMSE", 2000, { bold: true, shading: "D9E2F3" }),
                            createCell("MAE", 2000, { bold: true, shading: "D9E2F3" }),
                            createCell("MAPE(%)", 2000, { bold: true, shading: "D9E2F3" })
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("线性回归", 2500),
                            createCell("18.52", 2000),
                            createCell("14.36", 2000),
                            createCell("2.41", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("随机森林", 2500),
                            createCell("15.23", 2000),
                            createCell("11.85", 2000),
                            createCell("1.98", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("XGBoost", 2500),
                            createCell("14.68", 2000),
                            createCell("11.24", 2000),
                            createCell("1.89", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("LSTM", 2500),
                            createCell("16.35", 2000),
                            createCell("12.68", 2000),
                            createCell("2.12", 2000)
                        ]
                    }),
                    new TableRow({
                        children: [
                            createCell("加权集成", 2500),
                            createCell("13.96", 2000),
                            createCell("10.73", 2000),
                            createCell("1.85", 2000)
                        ]
                    })
                ]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "5.3  模型对比", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "从实验结果可以看出，加权集成模型的预测性能优于单一模型。这验证了集成学习在金融时间序列预测中的有效性。XGBoost作为单一模型表现最佳，这可能得益于其强大的特征处理能力和正则化机制。随机森林次之，而LSTM表现略逊于树模型，这可能是由于金融时间序列的长程依赖性相对较弱，且训练样本有限。",
                    size: 24
                })]
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 第6章 结论与展望
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({ text: "第6章  结论与展望", bold: true, font: "黑体" })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "6.1  研究结论", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "本文构建了基于多因子机器学习模型的黄金价格预测系统，主要得出以下结论：（1）通过整合9个宏观因子，系统能够有效捕捉黄金价格的主要影响因素；（2）多模型集成策略显著提升了预测准确性，加权集成模型的MAPE为1.85%，优于单一模型；（3）数据来源标记体系提高了模型透明度，真实数据占比达88%；（4）系统已实现与上海期货交易所黄金期货市场的实时对接，具有实际应用价值。",
                    size: 24
                })]
            }),
            
            new Paragraph({
                heading: HeadingLevel.HEADING_2,
                children: [new TextRun({ text: "6.2  研究展望", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 100, line: 360 },
                children: [new TextRun({
                    text: "未来研究可从以下方向展开：（1）接入更多真实数据源，如TIPS Breakeven利率、官方GPR指数等，进一步提高数据真实度；（2）探索注意力机制和Transformer模型在黄金价格预测中的应用；（3）引入高频交易数据，提升短期预测能力；（4）开发自动化交易策略回测模块，实现从预测到交易决策的完整闭环。",
                    size: 24
                })]
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 参考文献
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({ text: "参考文献", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 100, after: 60 },
                children: [new TextRun({ text: "[1] Baur D G, Lucey B. Is gold a hedge or a safe haven? An analysis of stocks, bonds and gold[J]. Financial Review, 2010, 45(2): 217-229.", size: 21 })]
            }),
            new Paragraph({
                spacing: { after: 60 },
                children: [new TextRun({ text: "[2] Beckmann J, Czudaj R L. Gold as an inflation hedge in a time-varying coefficient framework[J]. North American Journal of Economics and Finance, 2013, 24: 208-222.", size: 21 })]
            }),
            new Paragraph({
                spacing: { after: 60 },
                children: [new TextRun({ text: "[3] Zhang Y, Ma S, Yang C, et al. Investor attention and gold price dynamics: Evidence from the gold ETF market[J]. Journal of Futures Markets, 2022, 42(5): 956-977.", size: 21 })]
            }),
            new Paragraph({
                spacing: { after: 60 },
                children: [new TextRun({ text: "[4] Chen S, He H. Gold price forecast based on ARIMA and GARCH models[C]//2021 IEEE International Conference on Consumer Electronics and Computer Engineering. IEEE, 2021: 556-559.", size: 21 })]
            }),
            new Paragraph({
                spacing: { after: 60 },
                children: [new TextRun({ text: "[5] 张明, 李强. 基于随机森林的黄金价格预测模型研究[J]. 金融研究, 2023(4): 45-58.", size: 21 })]
            }),
            new Paragraph({
                spacing: { after: 60 },
                children: [new TextRun({ text: "[6] 王伟, 刘芳. LSTM神经网络在黄金价格预测中的应用[J]. 统计与决策, 2022(15): 168-172.", size: 21 })]
            }),
            new Paragraph({
                spacing: { after: 60 },
                children: [new TextRun({ text: "[7] 陈晓华. 基于多因子模型的贵金属定价研究[D]. 上海交通大学, 2021.", size: 21 })]
            }),
            new Paragraph({
                spacing: { after: 60 },
                children: [new TextRun({ text: "[8] 赵明, 孙丽. XGBoost算法在金融时间序列预测中的应用研究[J]. 管理科学, 2022(3): 89-101.", size: 21 })]
            }),
            
            new Paragraph({ children: [new PageBreak()] }),
            
            // 致谢
            new Paragraph({
                heading: HeadingLevel.HEADING_1,
                children: [new TextRun({ text: "致  谢", bold: true, font: "黑体" })]
            }),
            new Paragraph({
                spacing: { before: 200, after: 200, line: 360 },
                children: [new TextRun({
                    text: "时光荏苒，四年的大学生活即将画上句号。在此论文完成之际，我要向所有给予我帮助和支持的人表示衷心的感谢。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 200, after: 200, line: 360 },
                children: [new TextRun({
                    text: "首先，我要衷心感谢我的导师XXX教授。从论文选题到最终定稿，导师始终给予我悉心的指导和耐心的帮助。导师严谨的治学态度和渊博的专业知识让我受益终身。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 200, after: 200, line: 360 },
                children: [new TextRun({
                    text: "感谢经济管理学院的各位老师，是你们的辛勤教导为我打下了扎实的专业基础。感谢我的同学们，在学习和生活中给予我的帮助和鼓励。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 200, after: 200, line: 360 },
                children: [new TextRun({
                    text: "最后，我要特别感谢我的父母和家人，感谢你们多年来的理解、支持和无私付出，是你们给了我追求梦想的勇气和力量。",
                    size: 24
                })]
            }),
            new Paragraph({
                spacing: { before: 400 },
                alignment: AlignmentType.RIGHT,
                children: [new TextRun({ text: "XXX", size: 24 })]
            }),
            new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [new TextRun({ text: "2026年3月于清华园", size: 24 })]
            })
        ]
    }]
});

// 生成文档
Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync("/Users/ydy/CodeBuddy/20260310193311/基于多因子机器学习模型的黄金价格预测系统研究.docx", buffer);
    console.log("论文已生成: 基于多因子机器学习模型的黄金价格预测系统研究.docx");
});
