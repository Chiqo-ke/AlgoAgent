//+------------------------------------------------------------------+
//|                                      PythonSignalExecutor.mq5    |
//|                              AlgoAgent MT5 Integration v2.0      |
//|                              https://github.com/Chiqo-ke         |
//+------------------------------------------------------------------+
#property copyright "AlgoAgent"
#property link      "https://github.com/Chiqo-ke/AlgoAgent"
#property version   "2.00"
#property description "Expert Advisor to execute signals from Python backtester"
#property description "Compatible with SimBroker MT5 signal export format"
#property strict

//+------------------------------------------------------------------+
//| Input Parameters                                                  |
//+------------------------------------------------------------------+
input group "=== File Settings ==="
input string   SignalFile = "BT_20241018_120000_XAUUSD_H1_signals.csv"; // Signal CSV file (in MQL5/Files/)

input group "=== Risk Management ==="
input double   RiskPercent = 0.0;        // Risk % per trade (0 = use signal lot size)
input double   MaxLotSize = 10.0;        // Maximum lot size allowed

input group "=== Trading Settings ==="
input int      Slippage = 10;            // Max slippage in points
input int      MagicNumber = 20241019;   // Magic number for trades
input bool     CloseOppositeFirst = true; // Close opposite position before opening new

input group "=== Logging ==="
input bool     LogVerbose = true;        // Enable detailed logging
input bool     LogSignalDetails = true;  // Log each signal details

//+------------------------------------------------------------------+
//| Global Variables                                                  |
//+------------------------------------------------------------------+

// Signal data structure matching Python CSV export
struct SignalData
{
   datetime timestamp;      // Signal timestamp (bar open time)
   string   symbol;         // Trading symbol
   string   signal;         // BUY/SELL/EXIT/HOLD
   double   lot_size;       // Position size in lots
   double   stop_loss;      // Stop loss price (0 = none)
   double   take_profit;    // Take profit price (0 = none)
   string   signal_id;      // Unique signal identifier
   string   metadata;       // Additional data (JSON string)
};

// Global storage
SignalData signals[];           // Array of all loaded signals
int        totalSignals = 0;    // Total signals loaded
int        currentSignalIndex = 0; // Current processing position
bool       fileLoaded = false;  // File load status
datetime   lastBarTime = 0;     // Last processed bar time
int        tradesExecuted = 0;  // Trades executed counter
int        signalsProcessed = 0; // Signals processed counter

// Statistics
int        buySignals = 0;
int        sellSignals = 0;
int        exitSignals = 0;
int        holdSignals = 0;
int        skippedSignals = 0;

//+------------------------------------------------------------------+
//| Expert Initialization Function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   // Print startup banner
   Print("================================================================");
   Print("===       PythonSignalExecutor EA v2.0 Starting             ===");
   Print("================================================================");
   Print("Signal File: ", SignalFile);
   Print("Symbol: ", _Symbol);
   Print("Timeframe: ", EnumToString((ENUM_TIMEFRAMES)_Period));
   Print("Risk Percent: ", RiskPercent, "%");
   Print("Magic Number: ", MagicNumber);
   Print("================================================================");
   
   // Validate input parameters
   if(RiskPercent < 0.0 || RiskPercent > 100.0)
   {
      Print("ERROR: Invalid RiskPercent (must be 0-100)");
      return INIT_PARAMETERS_INCORRECT;
   }
   
   if(MaxLotSize <= 0.0)
   {
      Print("ERROR: Invalid MaxLotSize (must be > 0)");
      return INIT_PARAMETERS_INCORRECT;
   }
   
   // Load signal file
   if(!LoadSignalFile(SignalFile))
   {
      Print("ERROR: Failed to load signal file: ", SignalFile);
      Print("Please check:");
      Print("  1. File exists in MQL5/Files/ directory");
      Print("  2. File has correct CSV format");
      Print("  3. File is not open in another program");
      return INIT_FAILED;
   }
   
   // Validate signals loaded
   if(totalSignals == 0)
   {
      Print("ERROR: No signals found in file");
      return INIT_FAILED;
   }
   
   // Print load summary
   Print("================================================================");
   Print("Successfully loaded ", totalSignals, " signals");
   Print("Date range: ", TimeToString(signals[0].timestamp), 
         " to ", TimeToString(signals[totalSignals-1].timestamp));
   Print("Signal types: BUY=", buySignals, " SELL=", sellSignals, 
         " EXIT=", exitSignals, " HOLD=", holdSignals);
   Print("================================================================");
   
   fileLoaded = true;
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert Deinitialization Function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("================================================================");
   Print("===       PythonSignalExecutor EA Stopped                   ===");
   Print("================================================================");
   Print("Deinit reason: ", reason, " - ", GetDeinitReasonText(reason));
   Print("Signals processed: ", signalsProcessed, " / ", totalSignals);
   Print("Trades executed: ", tradesExecuted);
   Print("Signals skipped: ", skippedSignals);
   Print("================================================================");
}

//+------------------------------------------------------------------+
//| Expert Tick Function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Skip if file not loaded
   if(!fileLoaded || totalSignals == 0)
      return;
   
   // Get current bar open time
   datetime currentBarTime = iTime(_Symbol, _Period, 0);
   
   // Check if new bar opened
   if(currentBarTime == lastBarTime)
      return; // Still on same bar
   
   // New bar detected
   lastBarTime = currentBarTime;
   
   // Process signal(s) for this bar
   ProcessSignalsForBar(currentBarTime);
}

//+------------------------------------------------------------------+
//| Load Signal File from CSV                                         |
//+------------------------------------------------------------------+
bool LoadSignalFile(string filename)
{
   Print("Loading signal file: ", filename);
   
   // Open file for reading
   int fileHandle = FileOpen(filename, FILE_READ|FILE_CSV|FILE_ANSI, ',');
   
   if(fileHandle == INVALID_HANDLE)
   {
      Print("ERROR: Cannot open file. Error code: ", GetLastError());
      return false;
   }
   
   // Read and validate header
   if(!ValidateHeader(fileHandle))
   {
      FileClose(fileHandle);
      return false;
   }
   
   // Read signals
   int lineNumber = 1; // Start from 1 (header is line 0)
   
   while(!FileIsEnding(fileHandle))
   {
      SignalData signal;
      
      // Read CSV row
      string timestamp_str = FileReadString(fileHandle);
      string symbol_str = FileReadString(fileHandle);
      string signal_str = FileReadString(fileHandle);
      string lot_str = FileReadString(fileHandle);
      string sl_str = FileReadString(fileHandle);
      string tp_str = FileReadString(fileHandle);
      string id_str = FileReadString(fileHandle);
      string meta_str = FileReadString(fileHandle);
      
      // Skip empty lines
      if(timestamp_str == "" && symbol_str == "")
         continue;
      
      lineNumber++;
      
      // Parse timestamp (ISO 8601 format)
      signal.timestamp = ParseISO8601Timestamp(timestamp_str);
      if(signal.timestamp == 0)
      {
         Print("WARNING: Invalid timestamp at line ", lineNumber, ": ", timestamp_str);
         skippedSignals++;
         continue;
      }
      
      // Parse other fields
      signal.symbol = symbol_str;
      signal.signal = signal_str;
      signal.lot_size = StringToDouble(lot_str);
      signal.stop_loss = StringToDouble(sl_str);
      signal.take_profit = StringToDouble(tp_str);
      signal.signal_id = id_str;
      signal.metadata = meta_str;
      
      // Validate signal
      if(!ValidateSignal(signal, lineNumber))
      {
         skippedSignals++;
         continue;
      }
      
      // Add to array
      ArrayResize(signals, totalSignals + 1);
      signals[totalSignals] = signal;
      totalSignals++;
      
      // Count signal types
      if(signal.signal == "BUY") buySignals++;
      else if(signal.signal == "SELL") sellSignals++;
      else if(signal.signal == "EXIT") exitSignals++;
      else if(signal.signal == "HOLD") holdSignals++;
   }
   
   FileClose(fileHandle);
   
   Print("Loaded ", totalSignals, " valid signals");
   if(skippedSignals > 0)
      Print("Skipped ", skippedSignals, " invalid signals");
   
   return totalSignals > 0;
}

//+------------------------------------------------------------------+
//| Validate CSV Header                                               |
//+------------------------------------------------------------------+
bool ValidateHeader(int fileHandle)
{
   string header = FileReadString(fileHandle);
   
   // Expected header
   string expected = "timestamp";
   
   if(StringFind(header, expected) < 0)
   {
      Print("ERROR: Invalid CSV header. Expected to start with 'timestamp'");
      Print("Found: ", header);
      return false;
   }
   
   if(LogVerbose)
      Print("CSV Header validated: ", header);
   
   return true;
}

//+------------------------------------------------------------------+
//| Parse ISO 8601 Timestamp                                          |
//| Format: 2024-01-15T09:00:00+00:00                                |
//+------------------------------------------------------------------+
datetime ParseISO8601Timestamp(string timestamp_str)
{
   // Remove timezone suffix (+00:00 or Z)
   StringReplace(timestamp_str, "+00:00", "");
   StringReplace(timestamp_str, "Z", "");
   StringReplace(timestamp_str, "T", " "); // Replace T with space
   
   // Now format is: 2024-01-15 09:00:00
   datetime result = StringToTime(timestamp_str);
   
   return result;
}

//+------------------------------------------------------------------+
//| Validate Signal Data                                              |
//+------------------------------------------------------------------+
bool ValidateSignal(SignalData &signal, int lineNumber)
{
   // Check signal type
   if(signal.signal != "BUY" && signal.signal != "SELL" && 
      signal.signal != "EXIT" && signal.signal != "HOLD")
   {
      if(LogVerbose)
         Print("WARNING: Invalid signal type at line ", lineNumber, ": ", signal.signal);
      return false;
   }
   
   // Check lot size
   if(signal.lot_size < 0)
   {
      if(LogVerbose)
         Print("WARNING: Negative lot size at line ", lineNumber);
      return false;
   }
   
   // Check symbol (warning only)
   if(signal.symbol != _Symbol && LogVerbose)
   {
      Print("WARNING: Signal symbol (", signal.symbol, ") differs from EA symbol (", _Symbol, ")");
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Process Signals for Current Bar                                   |
//+------------------------------------------------------------------+
void ProcessSignalsForBar(datetime bar_time)
{
   // Search for signals matching this bar time
   for(int i = currentSignalIndex; i < totalSignals; i++)
   {
      // Check if signal timestamp matches current bar
      if(signals[i].timestamp == bar_time)
      {
         // Process this signal
         ExecuteSignal(signals[i]);
         signalsProcessed++;
         currentSignalIndex = i + 1;
      }
      else if(signals[i].timestamp > bar_time)
      {
         // Future signal, stop searching
         break;
      }
      else
      {
         // Past signal that was missed
         if(LogVerbose)
            Print("WARNING: Skipped past signal at ", TimeToString(signals[i].timestamp));
         signalsProcessed++;
         currentSignalIndex = i + 1;
      }
   }
}

//+------------------------------------------------------------------+
//| Execute Trading Signal                                            |
//+------------------------------------------------------------------+
void ExecuteSignal(SignalData &signal)
{
   // Log signal processing
   if(LogSignalDetails)
   {
      Print("--- Processing Signal ---");
      Print("Time: ", TimeToString(signal.timestamp));
      Print("Symbol: ", signal.symbol);
      Print("Signal: ", signal.signal);
      Print("Lot Size: ", DoubleToString(signal.lot_size, 2));
      Print("Stop Loss: ", DoubleToString(signal.stop_loss, 5));
      Print("Take Profit: ", DoubleToString(signal.take_profit, 5));
      Print("ID: ", signal.signal_id);
   }
   
   // Check symbol match
   if(signal.symbol != _Symbol)
   {
      if(LogVerbose)
         Print("WARNING: Signal symbol (", signal.symbol, ") does not match EA symbol (", _Symbol, ") - Skipping");
      return;
   }
   
   // Get current position info
   bool hasPosition = PositionSelect(_Symbol);
   ENUM_POSITION_TYPE posType = POSITION_TYPE_BUY; // Default
   
   if(hasPosition)
      posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   
   // Execute based on signal type
   if(signal.signal == "BUY")
   {
      // Close short position if exists
      if(hasPosition && posType == POSITION_TYPE_SELL && CloseOppositeFirst)
      {
         if(LogVerbose)
            Print("Closing SHORT position before opening LONG");
         ClosePosition();
         hasPosition = false;
      }
      
      // Open long position if no position
      if(!hasPosition || !CloseOppositeFirst)
      {
         double lotSize = CalculateLotSize(signal.lot_size);
         if(OpenPosition(ORDER_TYPE_BUY, lotSize, signal.stop_loss, signal.take_profit, signal.signal_id))
            tradesExecuted++;
      }
   }
   else if(signal.signal == "SELL")
   {
      // Close long position if exists
      if(hasPosition && posType == POSITION_TYPE_BUY && CloseOppositeFirst)
      {
         if(LogVerbose)
            Print("Closing LONG position before opening SHORT");
         ClosePosition();
         hasPosition = false;
      }
      
      // Open short position if no position
      if(!hasPosition || !CloseOppositeFirst)
      {
         double lotSize = CalculateLotSize(signal.lot_size);
         if(OpenPosition(ORDER_TYPE_SELL, lotSize, signal.stop_loss, signal.take_profit, signal.signal_id))
            tradesExecuted++;
      }
   }
   else if(signal.signal == "EXIT")
   {
      // Close any open position
      if(hasPosition)
      {
         if(LogVerbose)
            Print("Closing position (EXIT signal)");
         ClosePosition();
         tradesExecuted++;
      }
      else
      {
         if(LogVerbose)
            Print("No position to close (EXIT signal)");
      }
   }
   else if(signal.signal == "HOLD")
   {
      // No action needed
      if(LogVerbose)
         Print("HOLD signal - maintaining current state");
   }
}

//+------------------------------------------------------------------+
//| Calculate Lot Size Based on Risk                                 |
//+------------------------------------------------------------------+
double CalculateLotSize(double signalLotSize)
{
   double lotSize = signalLotSize;
   
   // If RiskPercent is set, calculate lot size based on account risk
   if(RiskPercent > 0.0)
   {
      double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      double riskAmount = accountBalance * RiskPercent / 100.0;
      
      // Get symbol specifications
      double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
      double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
      double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
      
      // Simple risk-based calculation (can be enhanced with SL distance)
      lotSize = riskAmount / (tickValue * 100); // Simplified calculation
      
      // Normalize to lot step
      lotSize = MathFloor(lotSize / lotStep) * lotStep;
      
      // Apply limits
      if(lotSize < minLot) lotSize = minLot;
      if(lotSize > maxLot) lotSize = maxLot;
   }
   
   // Apply maximum lot size limit
   if(lotSize > MaxLotSize)
      lotSize = MaxLotSize;
   
   // Validate against symbol limits
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   // Normalize
   lotSize = MathFloor(lotSize / lotStep) * lotStep;
   
   // Final validation
   if(lotSize < minLot)
   {
      if(LogVerbose)
         Print("WARNING: Lot size ", lotSize, " below minimum ", minLot, " - using minimum");
      lotSize = minLot;
   }
   
   if(lotSize > maxLot)
   {
      if(LogVerbose)
         Print("WARNING: Lot size ", lotSize, " above maximum ", maxLot, " - using maximum");
      lotSize = maxLot;
   }
   
   return lotSize;
}

//+------------------------------------------------------------------+
//| Open Position                                                     |
//+------------------------------------------------------------------+
bool OpenPosition(ENUM_ORDER_TYPE orderType, double lotSize, double stopLoss, double takeProfit, string comment)
{
   // Get current prices
   double price = 0;
   if(orderType == ORDER_TYPE_BUY)
      price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   else
      price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   // Normalize SL and TP
   double sl = NormalizePrice(stopLoss);
   double tp = NormalizePrice(takeProfit);
   
   // Prepare trade request
   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = lotSize;
   request.type = orderType;
   request.price = price;
   request.sl = sl;
   request.tp = tp;
   request.deviation = Slippage;
   request.magic = MagicNumber;
   request.comment = StringSubstr(comment, 0, 31); // MT5 comment limit
   request.type_filling = ORDER_FILLING_FOK;
   
   // Try FOK, if fails try IOC
   if(!OrderSend(request, result))
   {
      request.type_filling = ORDER_FILLING_IOC;
      if(!OrderSend(request, result))
      {
         request.type_filling = ORDER_FILLING_RETURN;
         OrderSend(request, result);
      }
   }
   
   // Check result
   if(result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED)
   {
      Print("✓ ", (orderType == ORDER_TYPE_BUY ? "LONG" : "SHORT"), 
            " position opened: ", lotSize, " lots at ", DoubleToString(price, _Digits),
            " | Ticket: ", result.order);
      if(sl > 0)
         Print("  Stop Loss: ", DoubleToString(sl, _Digits));
      if(tp > 0)
         Print("  Take Profit: ", DoubleToString(tp, _Digits));
      return true;
   }
   else
   {
      Print("✗ Failed to open position. Error: ", result.retcode, " - ", GetRetcodeDescription(result.retcode));
      Print("  Request: ", orderType == ORDER_TYPE_BUY ? "BUY" : "SELL", 
            " ", lotSize, " lots at ", DoubleToString(price, _Digits));
      return false;
   }
}

//+------------------------------------------------------------------+
//| Close Current Position                                            |
//+------------------------------------------------------------------+
bool ClosePosition()
{
   if(!PositionSelect(_Symbol))
   {
      if(LogVerbose)
         Print("No position to close");
      return false;
   }
   
   // Get position info
   long ticket = PositionGetInteger(POSITION_TICKET);
   double volume = PositionGetDouble(POSITION_VOLUME);
   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
   
   // Determine close price and order type
   double closePrice;
   ENUM_ORDER_TYPE closeOrderType;
   
   if(posType == POSITION_TYPE_BUY)
   {
      closePrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      closeOrderType = ORDER_TYPE_SELL;
   }
   else
   {
      closePrice = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      closeOrderType = ORDER_TYPE_BUY;
   }
   
   // Prepare close request
   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action = TRADE_ACTION_DEAL;
   request.position = ticket;
   request.symbol = _Symbol;
   request.volume = volume;
   request.type = closeOrderType;
   request.price = closePrice;
   request.deviation = Slippage;
   request.magic = MagicNumber;
   request.comment = "Close";
   request.type_filling = ORDER_FILLING_FOK;
   
   // Try FOK, if fails try IOC
   if(!OrderSend(request, result))
   {
      request.type_filling = ORDER_FILLING_IOC;
      if(!OrderSend(request, result))
      {
         request.type_filling = ORDER_FILLING_RETURN;
         OrderSend(request, result);
      }
   }
   
   // Check result
   if(result.retcode == TRADE_RETCODE_DONE)
   {
      double profit = PositionGetDouble(POSITION_PROFIT);
      Print("✓ ", (posType == POSITION_TYPE_BUY ? "LONG" : "SHORT"),
            " position closed: ", volume, " lots at ", DoubleToString(closePrice, _Digits),
            " | Profit: ", DoubleToString(profit, 2),
            " | Ticket: ", ticket);
      return true;
   }
   else
   {
      Print("✗ Failed to close position. Error: ", result.retcode, " - ", GetRetcodeDescription(result.retcode));
      return false;
   }
}

//+------------------------------------------------------------------+
//| Normalize Price to Symbol Digits                                 |
//+------------------------------------------------------------------+
double NormalizePrice(double price)
{
   if(price == 0.0)
      return 0.0;
   
   return NormalizeDouble(price, _Digits);
}

//+------------------------------------------------------------------+
//| Get Deinit Reason Text                                            |
//+------------------------------------------------------------------+
string GetDeinitReasonText(int reason)
{
   switch(reason)
   {
      case REASON_PROGRAM:     return "Expert Advisor terminated";
      case REASON_REMOVE:      return "Removed from chart";
      case REASON_RECOMPILE:   return "Recompiled";
      case REASON_CHARTCHANGE: return "Symbol or timeframe changed";
      case REASON_CHARTCLOSE:  return "Chart closed";
      case REASON_PARAMETERS:  return "Input parameters changed";
      case REASON_ACCOUNT:     return "Account changed";
      case REASON_TEMPLATE:    return "Template loaded";
      case REASON_INITFAILED:  return "Initialization failed";
      case REASON_CLOSE:       return "Terminal closed";
      default:                 return "Unknown reason";
   }
}

//+------------------------------------------------------------------+
//| Get Trade Return Code Description                                 |
//+------------------------------------------------------------------+
string GetRetcodeDescription(uint retcode)
{
   switch(retcode)
   {
      case TRADE_RETCODE_DONE:           return "Request completed";
      case TRADE_RETCODE_PLACED:         return "Order placed";
      case TRADE_RETCODE_DONE_PARTIAL:   return "Request partially completed";
      case TRADE_RETCODE_ERROR:          return "Request processing error";
      case TRADE_RETCODE_TIMEOUT:        return "Request timeout";
      case TRADE_RETCODE_INVALID:        return "Invalid request";
      case TRADE_RETCODE_INVALID_VOLUME: return "Invalid volume";
      case TRADE_RETCODE_INVALID_PRICE:  return "Invalid price";
      case TRADE_RETCODE_INVALID_STOPS:  return "Invalid stops";
      case TRADE_RETCODE_TRADE_DISABLED: return "Trading disabled";
      case TRADE_RETCODE_MARKET_CLOSED:  return "Market closed";
      case TRADE_RETCODE_NO_MONEY:       return "Not enough money";
      case TRADE_RETCODE_PRICE_CHANGED:  return "Price changed";
      case TRADE_RETCODE_PRICE_OFF:      return "No quotes";
      case TRADE_RETCODE_INVALID_EXPIRATION: return "Invalid expiration";
      case TRADE_RETCODE_ORDER_CHANGED:  return "Order changed";
      case TRADE_RETCODE_TOO_MANY_REQUESTS: return "Too many requests";
      case TRADE_RETCODE_NO_CHANGES:     return "No changes";
      case TRADE_RETCODE_SERVER_DISABLES_AT: return "Auto trading disabled by server";
      case TRADE_RETCODE_CLIENT_DISABLES_AT: return "Auto trading disabled by client";
      case TRADE_RETCODE_LOCKED:         return "Request locked";
      case TRADE_RETCODE_FROZEN:         return "Order or position frozen";
      case TRADE_RETCODE_INVALID_FILL:   return "Invalid fill type";
      case TRADE_RETCODE_CONNECTION:     return "No connection";
      case TRADE_RETCODE_ONLY_REAL:      return "Only real accounts allowed";
      case TRADE_RETCODE_LIMIT_ORDERS:   return "Orders limit reached";
      case TRADE_RETCODE_LIMIT_VOLUME:   return "Volume limit reached";
      default:                           return "Unknown error " + IntegerToString(retcode);
   }
}

//+------------------------------------------------------------------+
