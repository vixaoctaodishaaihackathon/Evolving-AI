#!/usr/bin/env python3
"""
Generate PowerPoint presentation for hackathon demo.
Requires: pip install python-pptx
"""

import os

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

def create_presentation():
    """Create the hackathon presentation."""
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    
    # Define colors
    BLUE = RGBColor(41, 128, 185)
    DARK_BLUE = RGBColor(44, 62, 80)
    LIGHT_BLUE = RGBColor(52, 152, 219)
    GREEN = RGBColor(39, 174, 96)
    ORANGE = RGBColor(230, 126, 34)
    RED = RGBColor(231, 76, 60)
    WHITE = RGBColor(255, 255, 255)
    GRAY = RGBColor(149, 165, 166)

    def style_textbox(shape, text, size, color, bold=False, align=PP_ALIGN.LEFT):
        frame = shape.text_frame
        frame.word_wrap = True
        frame.margin_left = Pt(8)
        frame.margin_right = Pt(8)
        frame.margin_top = Pt(6)
        frame.margin_bottom = Pt(6)
        frame.clear()
        p = frame.paragraphs[0]
        p.text = text
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = color
        p.alignment = align
        return p
    
    # Slide 1: Title
    slide1 = prs.slides.add_slide(prs.slide_layouts[6])
    
    # Add background shape
    bg1 = slide1.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = DARK_BLUE
    bg1.line.fill.background()
    
    # Add decorative accent
    accent1 = slide1.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.5))
    accent1.fill.solid()
    accent1.fill.fore_color.rgb = ORANGE
    accent1.line.fill.background()
    
    title = slide1.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(8.8), Inches(0.8))
    style_textbox(title, "AI Supply Chain Helper", 28, WHITE, bold=True, align=PP_ALIGN.CENTER)

    subtitle = slide1.shapes.add_textbox(Inches(0.6), Inches(1.7), Inches(8.8), Inches(0.7))
    style_textbox(subtitle, "Smart System to Fix Supply Chain Problems", 20, LIGHT_BLUE, align=PP_ALIGN.CENTER)
    
    # Add colored box for problem
    problem_box = slide1.shapes.add_shape(1, Inches(0.7), Inches(2.7), Inches(8.6), Inches(3.4))
    problem_box.fill.solid()
    problem_box.fill.fore_color.rgb = BLUE
    problem_box.line.fill.background()
    
    problem = slide1.shapes.add_textbox(Inches(0.9), Inches(3.0), Inches(8.1), Inches(2.7))
    style_textbox(
        problem,
        "Problem: Supply chains lose $400M every day when disruption hits.\n\nSolution: AI finds the issue, maps affected suppliers, and responds automatically before the bottleneck spreads.",
        17,
        WHITE,
        align=PP_ALIGN.CENTER,
    )
    
    # Slide 2: Architecture
    slide2 = prs.slides.add_slide(prs.slide_layouts[6])
    
    # Background
    bg2 = slide2.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(7.5))
    bg2.fill.solid()
    bg2.fill.fore_color.rgb = WHITE
    bg2.line.fill.background()
    
    # Header bar
    header2 = slide2.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.8))
    header2.fill.solid()
    header2.fill.fore_color.rgb = BLUE
    header2.line.fill.background()
    
    title2 = slide2.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.6))
    title2_frame = title2.text_frame
    title2_frame.text = "How It Works"
    title2_para = title2_frame.paragraphs[0]
    title2_para.font.size = Pt(32)
    title2_para.font.bold = True
    title2_para.font.color.rgb = WHITE
    title2_para.alignment = PP_ALIGN.CENTER
    
    # Step boxes with colors
    step1_box = slide2.shapes.add_shape(1, Inches(0.35), Inches(1.2), Inches(4.35), Inches(2.7))
    step1_box.fill.solid()
    step1_box.fill.fore_color.rgb = LIGHT_BLUE
    step1_box.line.fill.background()
    
    step2_box = slide2.shapes.add_shape(1, Inches(5.15), Inches(1.2), Inches(4.35), Inches(2.7))
    step2_box.fill.solid()
    step2_box.fill.fore_color.rgb = GREEN
    step2_box.line.fill.background()
    
    step3_box = slide2.shapes.add_shape(1, Inches(0.35), Inches(4.1), Inches(4.35), Inches(2.7))
    step3_box.fill.solid()
    step3_box.fill.fore_color.rgb = ORANGE
    step3_box.line.fill.background()
    
    step4_box = slide2.shapes.add_shape(1, Inches(5.15), Inches(4.1), Inches(4.35), Inches(2.7))
    step4_box.fill.solid()
    step4_box.fill.fore_color.rgb = RED
    step4_box.line.fill.background()
    
    # Step 1 text
    step1_text = slide2.shapes.add_textbox(Inches(0.55), Inches(1.35), Inches(3.9), Inches(2.3))
    step1_frame = step1_text.text_frame
    step1_frame.word_wrap = True
    step1_frame.margin_left = Pt(8)
    step1_frame.margin_right = Pt(8)
    step1_frame.margin_top = Pt(6)
    step1_frame.margin_bottom = Pt(6)
    step1_frame.text = "Step 1: Collect Data\n• Sensors on ships send GPS and cargo info\n• Market prices tracked in real time\n• Fast event messaging"
    step1_para = step1_frame.paragraphs[0]
    step1_para.font.size = Pt(12)
    step1_para.font.color.rgb = WHITE
    
    # Step 2 text
    step2_text = slide2.shapes.add_textbox(Inches(5.35), Inches(1.35), Inches(3.9), Inches(2.3))
    step2_frame = step2_text.text_frame
    step2_frame.word_wrap = True
    step2_frame.margin_left = Pt(8)
    step2_frame.margin_right = Pt(8)
    step2_frame.margin_top = Pt(6)
    step2_frame.margin_bottom = Pt(6)
    step2_frame.text = "Step 2: Store Information\n• Stores price history and trends\n• Maps all suppliers\n• Shows supply connections"
    step2_para = step2_frame.paragraphs[0]
    step2_para.font.size = Pt(12)
    step2_para.font.color.rgb = WHITE
    
    # Step 3 text
    step3_text = slide2.shapes.add_textbox(Inches(0.55), Inches(4.25), Inches(3.9), Inches(2.2))
    step3_frame = step3_text.text_frame
    step3_frame.word_wrap = True
    step3_frame.margin_left = Pt(8)
    step3_frame.margin_right = Pt(8)
    step3_frame.margin_top = Pt(6)
    step3_frame.margin_bottom = Pt(6)
    step3_frame.text = "Step 3: AI Agents Work\n• Finds price spikes\n• Checks affected suppliers\n• Finds backup routes\n• Applies safety rules"
    step3_para = step3_frame.paragraphs[0]
    step3_para.font.size = Pt(12)
    step3_para.font.color.rgb = WHITE
    
    # Step 4 text
    step4_text = slide2.shapes.add_textbox(Inches(5.35), Inches(4.25), Inches(3.9), Inches(2.2))
    step4_frame = step4_text.text_frame
    step4_frame.word_wrap = True
    step4_frame.margin_left = Pt(8)
    step4_frame.margin_right = Pt(8)
    step4_frame.margin_top = Pt(6)
    step4_frame.margin_bottom = Pt(6)
    step4_frame.text = "Step 4: Learn & Improve\n• Remembers what worked\n• Gets smarter\n• Adapts automatically"
    step4_para = step4_frame.paragraphs[0]
    step4_para.font.size = Pt(12)
    step4_para.font.color.rgb = WHITE
    
    # Slide 3: Technical Stack
    slide3 = prs.slides.add_slide(prs.slide_layouts[6])
    
    # Background
    bg3 = slide3.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(7.5))
    bg3.fill.solid()
    bg3.fill.fore_color.rgb = WHITE
    bg3.line.fill.background()
    
    # Header
    header3 = slide3.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.8))
    header3.fill.solid()
    header3.fill.fore_color.rgb = GREEN
    header3.line.fill.background()
    
    title3 = slide3.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.6))
    title3_frame = title3.text_frame
    title3_frame.text = "Tools We Use"
    title3_para = title3_frame.paragraphs[0]
    title3_para.font.size = Pt(32)
    title3_para.font.bold = True
    title3_para.font.color.rgb = WHITE
    title3_para.alignment = PP_ALIGN.CENTER
    
    # Left box
    stack_box = slide3.shapes.add_shape(1, Inches(0.3), Inches(1.2), Inches(4.5), Inches(5.8))
    stack_box.fill.solid()
    stack_box.fill.fore_color.rgb = LIGHT_BLUE
    stack_box.line.fill.background()
    
    stack = slide3.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(4.1), Inches(5.4))
    stack_frame = stack.text_frame
    stack_frame.text = """Main Tools:
• LangGraph - Manages AI agents
• Kafka/Redis - Fast messages
• ClickHouse/PG - Stores data
• Neo4j/PG - Maps suppliers
• Guardrails - Safety rules
• Phoenix - Tracks performance

Cool Features:
1. See All Connections
   - Shows all supplier levels
   - Finds dependencies
   - Spots weak points

2. Self-Improving
   - Learns from decisions
   - Gets better over time
   - Remembers what worked"""
    stack_para = stack_frame.paragraphs[0]
    stack_para.font.size = Pt(12)
    stack_para.font.color.rgb = WHITE
    
    # Right box
    innovations_box = slide3.shapes.add_shape(1, Inches(5.2), Inches(1.2), Inches(4.5), Inches(5.8))
    innovations_box.fill.solid()
    innovations_box.fill.fore_color.rgb = ORANGE
    innovations_box.line.fill.background()
    
    innovations = slide3.shapes.add_textbox(Inches(5.4), Inches(1.4), Inches(4.1), Inches(5.4))
    innovations_frame = innovations.text_frame
    innovations_frame.text = """3. Works Anywhere
   - Local: Your computer
   - Cloud: Render/Railway
   - Switches automatically

4. Safety Rules
   - Won't spend >$50K alone
   - Won't pay too much extra
   - Checks risky countries
   - Asks human for big decisions

5. Very Fast
   - Finds problems <1 second
   - Works with live data
   - No waiting for batches"""
    innovations_para = innovations_frame.paragraphs[0]
    innovations_para.font.size = Pt(12)
    innovations_para.font.color.rgb = WHITE
    
    # Slide 4: Demo
    slide4 = prs.slides.add_slide(prs.slide_layouts[6])
    
    # Background
    bg4 = slide4.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(7.5))
    bg4.fill.solid()
    bg4.fill.fore_color.rgb = WHITE
    bg4.line.fill.background()
    
    # Header
    header4 = slide4.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.8))
    header4.fill.solid()
    header4.fill.fore_color.rgb = RED
    header4.line.fill.background()
    
    title4 = slide4.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.6))
    title4_frame = title4.text_frame
    title4_frame.text = "Live Demo: When Ships Get Stuck"
    title4_para = title4_frame.paragraphs[0]
    title4_para.font.size = Pt(32)
    title4_para.font.bold = True
    title4_para.font.color.rgb = WHITE
    title4_para.alignment = PP_ALIGN.CENTER
    
    # Step boxes
    demo1_box = slide4.shapes.add_shape(1, Inches(0.3), Inches(1.2), Inches(4.5), Inches(1.4))
    demo1_box.fill.solid()
    demo1_box.fill.fore_color.rgb = RED
    demo1_box.line.fill.background()
    
    demo2_box = slide4.shapes.add_shape(1, Inches(5.2), Inches(1.2), Inches(4.5), Inches(1.4))
    demo2_box.fill.solid()
    demo2_box.fill.fore_color.rgb = ORANGE
    demo2_box.line.fill.background()
    
    demo3_box = slide4.shapes.add_shape(1, Inches(0.3), Inches(2.8), Inches(4.5), Inches(1.4))
    demo3_box.fill.solid()
    demo3_box.fill.fore_color.rgb = GREEN
    demo3_box.line.fill.background()
    
    demo4_box = slide4.shapes.add_shape(1, Inches(5.2), Inches(2.8), Inches(4.5), Inches(1.4))
    demo4_box.fill.solid()
    demo4_box.fill.fore_color.rgb = BLUE
    demo4_box.line.fill.background()
    
    demo5_box = slide4.shapes.add_shape(1, Inches(0.3), Inches(4.4), Inches(9.4), Inches(2.6))
    demo5_box.fill.solid()
    demo5_box.fill.fore_color.rgb = DARK_BLUE
    demo5_box.line.fill.background()
    
    # Demo texts
    demo1 = slide4.shapes.add_textbox(Inches(0.5), Inches(1.3), Inches(4.1), Inches(1.2))
    demo1_frame = demo1.text_frame
    demo1_frame.text = "Step 1: Find Problem\n   ALERT: Price spike 75% on Suez!"
    demo1_para = demo1_frame.paragraphs[0]
    demo1_para.font.size = Pt(12)
    demo1_para.font.color.rgb = WHITE
    
    demo2 = slide4.shapes.add_textbox(Inches(5.4), Inches(1.3), Inches(4.1), Inches(1.2))
    demo2_frame = demo2.text_frame
    demo2_frame.text = "Step 2: Check Impact\n   4 suppliers, $26.7M at risk"
    demo2_para = demo2_frame.paragraphs[0]
    demo2_para.font.size = Pt(12)
    demo2_para.font.color.rgb = WHITE
    
    demo3 = slide4.shapes.add_textbox(Inches(0.5), Inches(2.9), Inches(4.1), Inches(1.2))
    demo3_frame = demo3.text_frame
    demo3_frame.text = "Step 3: Find Solution\n   Use Saigon Assembly, $42K, 12 days"
    demo3_para = demo3_frame.paragraphs[0]
    demo3_para.font.size = Pt(12)
    demo3_para.font.color.rgb = WHITE
    
    demo4 = slide4.shapes.add_textbox(Inches(5.4), Inches(2.9), Inches(4.1), Inches(1.2))
    demo4_frame = demo4.text_frame
    demo4_frame.text = "Step 4: Safety Check\n   ✓ Under $50K, ✓ Low risk\n   Status: FIXED AUTOMATICALLY"
    demo4_para = demo4_frame.paragraphs[0]
    demo4_para.font.size = Pt(12)
    demo4_para.font.color.rgb = WHITE
    
    demo5 = slide4.shapes.add_textbox(Inches(0.5), Inches(4.5), Inches(8.6), Inches(2.2))
    demo5_frame = demo5.text_frame
    demo5_frame.text = "Step 5: Learn from It\n   System improved (generation 8) | Risk reduced by 45% | Saved 12 days of delay"
    demo5_para = demo5_frame.paragraphs[0]
    demo5_para.font.size = Pt(14)
    demo5_para.font.color.rgb = WHITE
    demo5_para.alignment = PP_ALIGN.CENTER
    
    # Slide 5: Dashboard
    slide5 = prs.slides.add_slide(prs.slide_layouts[6])
    
    # Background
    bg5 = slide5.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(7.5))
    bg5.fill.solid()
    bg5.fill.fore_color.rgb = WHITE
    bg5.line.fill.background()
    
    # Header
    header5 = slide5.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.8))
    header5.fill.solid()
    header5.fill.fore_color.rgb = LIGHT_BLUE
    header5.line.fill.background()
    
    title5 = slide5.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.6))
    title5_frame = title5.text_frame
    title5_frame.text = "Web Dashboard"
    title5_para = title5_frame.paragraphs[0]
    title5_para.font.size = Pt(32)
    title5_para.font.bold = True
    title5_para.font.color.rgb = WHITE
    title5_para.alignment = PP_ALIGN.CENTER
    
    # Feature boxes
    feat1_box = slide5.shapes.add_shape(1, Inches(0.3), Inches(1.2), Inches(4.5), Inches(2.8))
    feat1_box.fill.solid()
    feat1_box.fill.fore_color.rgb = BLUE
    feat1_box.line.fill.background()
    
    feat2_box = slide5.shapes.add_shape(1, Inches(5.2), Inches(1.2), Inches(4.5), Inches(2.8))
    feat2_box.fill.solid()
    feat2_box.fill.fore_color.rgb = GREEN
    feat2_box.line.fill.background()
    
    feat3_box = slide5.shapes.add_shape(1, Inches(0.3), Inches(4.2), Inches(4.5), Inches(2.8))
    feat3_box.fill.solid()
    feat3_box.fill.fore_color.rgb = ORANGE
    feat3_box.line.fill.background()
    
    # Command box
    cmd_box = slide5.shapes.add_shape(1, Inches(5.2), Inches(4.2), Inches(4.5), Inches(2.8))
    cmd_box.fill.solid()
    cmd_box.fill.fore_color.rgb = DARK_BLUE
    cmd_box.line.fill.background()
    
    # Feature texts
    feat1 = slide5.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(4.1), Inches(2.4))
    feat1_frame = feat1.text_frame
    feat1_frame.text = "Interactive Map\n  • Drag supplier nodes\n  • See dangerous routes\n  • Find weak points (red)"
    feat1_para = feat1_frame.paragraphs[0]
    feat1_para.font.size = Pt(13)
    feat1_para.font.color.rgb = WHITE
    
    feat2 = slide5.shapes.add_textbox(Inches(5.4), Inches(1.4), Inches(4.1), Inches(2.4))
    feat2_frame = feat2.text_frame
    feat2_frame.text = "Live Updates\n  • Watch ships move\n  • See price changes\n  • Get problem alerts"
    feat2_para = feat2_frame.paragraphs[0]
    feat2_para.font.size = Pt(13)
    feat2_para.font.color.rgb = WHITE
    
    feat3 = slide5.shapes.add_textbox(Inches(0.5), Inches(4.4), Inches(4.1), Inches(2.4))
    feat3_frame = feat3.text_frame
    feat3_frame.text = "Try It Yourself\n  • Simulate Blockade\n  • Watch AI decisions\n  • See human checks"
    feat3_para = feat3_frame.paragraphs[0]
    feat3_para.font.size = Pt(13)
    feat3_para.font.color.rgb = WHITE
    
    cmd = slide5.shapes.add_textbox(Inches(5.4), Inches(4.4), Inches(4.1), Inches(2.4))
    cmd_frame = cmd.text_frame
    cmd_frame.text = "How to Run:\n\nType: uvicorn web.server:app --port 8000\n\nOpen: http://127.0.0.1:8000"
    cmd_para = cmd_frame.paragraphs[0]
    cmd_para.font.size = Pt(13)
    cmd_para.font.color.rgb = WHITE
    
    # Slide 6: Cloud Deployment
    slide6 = prs.slides.add_slide(prs.slide_layouts[6])
    
    # Background
    bg6 = slide6.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(7.5))
    bg6.fill.solid()
    bg6.fill.fore_color.rgb = WHITE
    bg6.line.fill.background()
    
    # Header
    header6 = slide6.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.8))
    header6.fill.solid()
    header6.fill.fore_color.rgb = ORANGE
    header6.line.fill.background()
    
    title6 = slide6.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.6))
    title6_frame = title6.text_frame
    title6_frame.text = "Cloud Deployment"
    title6_para = title6_frame.paragraphs[0]
    title6_para.font.size = Pt(32)
    title6_para.font.bold = True
    title6_para.font.color.rgb = WHITE
    title6_para.alignment = PP_ALIGN.CENTER
    
    # Left box
    cloud_box = slide6.shapes.add_shape(1, Inches(0.3), Inches(1.2), Inches(4.5), Inches(5.8))
    cloud_box.fill.solid()
    cloud_box.fill.fore_color.rgb = BLUE
    cloud_box.line.fill.background()
    
    cloud = slide6.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(4.1), Inches(5.4))
    cloud_frame = cloud.text_frame
    cloud_frame.text = """Run on Your Computer:
   docker-compose up -d
   python run_demo.py

   What it uses:
   • Kafka (messages)
   • ClickHouse (data)
   • Neo4j (supplier map)
   • Phoenix (tracking)

Run in Cloud:
   Render or Railway
   No code changes!

   What it uses:
   • PostgreSQL (data)
   • Redis (messages)
   • Web Service
   • Background Worker"""
    cloud_para = cloud_frame.paragraphs[0]
    cloud_para.font.size = Pt(12)
    cloud_para.font.color.rgb = WHITE
    
    # Right box
    comparison_box = slide6.shapes.add_shape(1, Inches(5.2), Inches(1.2), Inches(4.5), Inches(5.8))
    comparison_box.fill.solid()
    comparison_box.fill.fore_color.rgb = GREEN
    comparison_box.line.fill.background()
    
    comparison = slide6.shapes.add_textbox(Inches(5.4), Inches(1.4), Inches(4.1), Inches(5.4))
    comparison_frame = comparison.text_frame
    comparison_frame.text = """How It Adapts:

Feature          Your Computer   Cloud
─────────────────────────────────────
Data Storage     ClickHouse      PostgreSQL
Supplier Map     Neo4j           PostgreSQL
Messages         Kafka           Redis
File Storage     Your Disk       Cloud Storage

Automatic Switch:
   If cloud settings found:
       Use cloud databases
   Otherwise:
       Use local databases

Ready for Production:
• Runs all the time
• Stops safely
• Easy to configure"""
    comparison_para = comparison_frame.paragraphs[0]
    comparison_para.font.size = Pt(11)
    comparison_para.font.color.rgb = WHITE
    
    # Slide 7: Impact
    slide7 = prs.slides.add_slide(prs.slide_layouts[6])
    
    # Background
    bg7 = slide7.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(7.5))
    bg7.fill.solid()
    bg7.fill.fore_color.rgb = WHITE
    bg7.line.fill.background()
    
    # Header
    header7 = slide7.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(0.8))
    header7.fill.solid()
    header7.fill.fore_color.rgb = DARK_BLUE
    header7.line.fill.background()
    
    title7 = slide7.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.6))
    title7_frame = title7.text_frame
    title7_frame.text = "Results & Next Steps"
    title7_para = title7_frame.paragraphs[0]
    title7_para.font.size = Pt(32)
    title7_para.font.bold = True
    title7_para.font.color.rgb = WHITE
    title7_para.alignment = PP_ALIGN.CENTER
    
    # Left box
    impact_box = slide7.shapes.add_shape(1, Inches(0.3), Inches(1.2), Inches(4.5), Inches(5.8))
    impact_box.fill.solid()
    impact_box.fill.fore_color.rgb = GREEN
    impact_box.line.fill.background()
    
    impact = slide7.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(4.1), Inches(5.4))
    impact_frame = impact.text_frame
    impact_frame.text = """What We Achieved:
• Finds problems <1 second
• Sees all supplier connections
• Saves 51% costs ($42K vs $85K)
• Reduces risk by 45%
• Learned 8 times (got smarter)
• Deploys in under 5 minutes

Why It's Better:
1. Works in Real-Time
   (No waiting for batches)

2. Sees Everything
   (Not just first-level)

3. Keeps Learning
   (Gets better over time)

4. Safe to Use
   (Won't make big mistakes)

5. Cloud Ready
   (Works on Render/Railway)"""
    impact_para = impact_frame.paragraphs[0]
    impact_para.font.size = Pt(12)
    impact_para.font.color.rgb = WHITE
    
    # Right box
    future_box = slide7.shapes.add_shape(1, Inches(5.2), Inches(1.2), Inches(4.5), Inches(5.8))
    future_box.fill.solid()
    future_box.fill.fore_color.rgb = LIGHT_BLUE
    future_box.line.fill.background()
    
    future = slide7.shapes.add_textbox(Inches(5.4), Inches(1.4), Inches(4.1), Inches(5.4))
    future_frame = future.text_frame
    future_frame.text = """Future Plans:
• Add More AI Models
  (Better negotiation)

• Predict Problems
  (Use ML forecasting)

• Blockchain Records
  (Permanent contract logs)

• Better Dashboard
  (More data views)

Conclusion:
This is a real system that
solves a big global problem.
It uses smart AI and works
in the cloud right now.

Ready to Use Today!"""
    future_para = future_frame.paragraphs[0]
    future_para.font.size = Pt(12)
    future_para.font.color.rgb = WHITE
    
    # Save presentation to a fresh file path to avoid locked PowerPoint copies
    output_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(output_dir, 'Hackathon_Presentation_Updated.pptx')
    prs.save(out_path)
    print(f"Presentation created: {out_path}")

if __name__ == "__main__":
    create_presentation()
