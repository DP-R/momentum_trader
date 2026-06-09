import pandas as pd

class TradePlanner:
    def __init__(self, config, regime):
        self.config = config
        self.regime = regime

    def display_trade_plan(self, row, label, risk_amount_rs, stop_widen_atr):
        entry_price = row['Price']
        atr = row['ATR']
        
        stop_loss = None
        t1_target = entry_price + 1.5 * atr
        t2_target = entry_price + 3 * atr
        
        if label == "Breakout":
            stop_loss = row.get('Breakout_Info', {}).get('stop_loss')
        elif label == "Pullback":
            stop_loss = row.get('Pullback_Info', {}).get('stop_loss')
            swing_high = row.get('Pullback_Info', {}).get('swing_high')
            if swing_high and not pd.isna(swing_high) and swing_high > entry_price:
                t1_target = swing_high

        if stop_loss is None or pd.isna(stop_loss):
            stop_loss = entry_price - atr * (1 + stop_widen_atr)
        else:
            if stop_widen_atr > 0:
                stop_loss = stop_loss - (atr * stop_widen_atr)

        stop_distance_pct = ((entry_price - stop_loss) / entry_price) * 100

        if stop_distance_pct > 8.0: # Allow up to 8% for midcaps as per document
            return f"{label} [{row['Ticker']}] SKIP: Stop loss too wide ({stop_distance_pct:.1f}%).", None

        risk_per_share = entry_price - stop_loss
        if risk_per_share <= 0:
            return f"{label} [{row['Ticker']}] SKIP: Invalid stop level.", None

        quantity = int(risk_amount_rs // risk_per_share)
        if quantity < 1:
            return f"{label} [{row['Ticker']}] SKIP: Position size too small after risk sizing.", None

        position_value = quantity * entry_price
        trade_plan = (
            f"{label} [{row['Ticker']}] Price: ₹{entry_price:.2f} | ATR%: {row['ATR_%']:.2f}% | Vol Surge: {row['Vol_Surge']:.1f}x\n"
            f"   ► Buy {quantity} shares | Cost: ₹{position_value:,.2f} | Risk: ₹{risk_amount_rs:,.0f}\n"
            f"   ► Stop Loss: ₹{stop_loss:.2f} | T1: ₹{t1_target:.2f} | T2: ₹{t2_target:.2f}\n"
            f"   ► Rule: If T1 hits, move stop to breakeven. Trail remaining at 10-EMA or prior swing low.\n"
            f"   ► Notes: Check earnings/settings/SEBI news before entry."
        )
        
        plan_dict = {
            "Strategy": label,
            "Ticker": row['Ticker'],
            "Entry_Price": entry_price,
            "Quantity": quantity,
            "Cost": position_value,
            "Stop_Loss": stop_loss,
            "T1": t1_target,
            "T2": t2_target,
            "ATR": atr
        }
        return trade_plan, plan_dict

    def generate_trade_plans(self, screener_df):
        risk_amount_rs = self.config.CAPITAL * self.config.RISK_PER_TRADE
        
        if self.regime.get("reduce_size_50_nifty") or self.regime.get("reduce_size_50_vix"):
            risk_amount_rs *= 0.5
        elif self.regime.get("reduce_size_25_vix"):
            risk_amount_rs *= 0.75

        stop_widen_atr = self.regime.get("stop_widen_atr", 0.0)

        momentum_candidates = screener_df.head(5)
        
        if 'Breakout_Candidate' in screener_df.columns:
            if self.regime.get("no_breakouts") or self.regime.get("mean_reversion_preferred"):
                breakout_candidates = pd.DataFrame()
            else:
                breakout_candidates = screener_df[screener_df['Breakout_Candidate']].sort_values(by='Vol_Surge', ascending=False).head(3)
        else:
            breakout_candidates = pd.DataFrame()
            
        if 'Pullback_Candidate' in screener_df.columns and 'RSI2' in screener_df.columns:
            pullback_candidates = screener_df[screener_df['Pullback_Candidate']].sort_values(by='RSI2').head(3)
        else:
            pullback_candidates = pd.DataFrame()

        trade_plans_str = []
        trade_plans_data = []

        def process_row(row, label):
            plan_str, plan_dict = self.display_trade_plan(row, label, risk_amount_rs, stop_widen_atr)
            trade_plans_str.append(plan_str)
            if plan_dict:
                trade_plans_data.append(plan_dict)

        for _, row in momentum_candidates.iterrows():
            process_row(row, "Momentum")

        for _, row in breakout_candidates.iterrows():
            process_row(row, "Breakout")

        for _, row in pullback_candidates.iterrows():
            process_row(row, "Pullback")

        return trade_plans_str, trade_plans_data