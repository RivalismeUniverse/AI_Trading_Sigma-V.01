# ai_logger.py - SIMPLE VERSION
async def report_decision(self, indicators, decision, order_id=None, confidence=None):
    """Format EXACT seperti contoh WEEX"""
    
    # INPUT: seperti contoh kedua WEEX
    input_data = {
        "prompt": "Analyze market indicators and generate trading signal",
        "data": {
            "RSI_14": indicators.get('rsi'),
            "MC_PROBABILITY": indicators.get('mc_probability'),
            "GK_VOLATILITY": indicators.get('gk_volatility'),
            "Z_SCORE": indicators.get('z_score')
        }
    }
    
    # OUTPUT: seperti contoh kedua WEEX
    output_data = {
        "signal": "BUY" if "LONG" in decision else "SELL",
        "confidence": float(confidence or 0.5),
        "reason": f"RSI: {indicators.get('rsi', 'N/A')}, MC: {indicators.get('mc_probability', 0):.1%}"
    }
    
    # EXPLANATION: simple & clear
    explanation = (
        f"Technical analysis shows RSI at {indicators.get('rsi', 'N/A')} "
        f"and Monte Carlo probability at {indicators.get('mc_probability', 0)*100:.1f}%. "
        f"Market conditions support a {output_data['signal']} signal."
    )
    
    # Kirim dengan parameter BENAR
    await self.weex.upload_ai_log(
        orderId=order_id,
        stage="Decision Making",  # PAKAI INI, jangan "Decision Support"
        model=self.model_name,
        input=input_data,  
        output=output_data,  
        explanation=explanation
    )
