//+------------------------------------------------------------------+
//|                                      PythonSignalExecutor_Multi.mq5 |
//|                              AlgoAgent MT5 Integration v3.0      |
//|                              https://github.com/Chiqo-ke         |
//+------------------------------------------------------------------+
#property copyright "AlgoAgent"
#property link      "https://github.com/Chiqo-ke/AlgoAgent"
#property version   "3.00"
#property description "Expert Advisor to execute signals from multiple Python backtest CSV files"
#property description "Scans folder and processes all matching signal files"
#property strict

//+------------------------------------------------------------------+
//| Input Parameters                                                  |
//+------------------------------------------------------------------+
input group "=== File Settings ==="
input string   SignalsFolder = "Experts/signals/";    // Subfolder within MQL5 folder (relative path)
input string   FolderPattern = "BT_*.csv";            // File pattern to match (e.g., "BT_*.csv", "XAUUSD_*.csv")
input string   SpecificFile = "";                     // Leave empty to scan folder, or specify single file
input bool     ProcessAllFiles = true;                // Process all matching files in sequence
input bool     SortByDate = true;                     // Sort files by date (chronological order)

input group "=== Risk Management ==="
input double   RiskPercent = 0.0;        // Risk % per trade (0 = use signal lot size)
input double   MaxLotSize = 10.0;        // Maximum lot size allowed
input bool     ResetEquityBetweenFiles = false; // Reset to initial deposit between files

input group "=== Trading Settings ==="
input int      Slippage = 10;            // Max slippage in points
input int      MagicNumber = 20251019;   // Magic number for trades
input bool     CloseOppositeFirst = true; // Close opposite position before opening new

input group "=== Logging ==="
input bool     LogVerbose = true;        // Enable detailed logging
input bool     LogSignalDetails = false; // Log each signal details (can be verbose)
input bool     LogFileList = true;       // Log list of files found

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
   string   source_file;    // Source CSV filename
};

// File tracking
struct FileInfo
{
   string filename;
   datetime file_date;
   int signal_count;
   bool processed;
};

// Global storage
SignalData signals[];           // Array of all loaded signals
FileInfo files[];               // Array of found files
int        totalSignals = 0;    // Total signals loaded
int        totalFiles = 0;      // Total files found
int        currentSignalIndex = 0; // Current processing position
int        currentFileIndex = 0;   // Current file being processed
bool       filesLoaded = false; // Files load status
datetime   lastBarTime = 0;     // Last processed bar time
int        tradesExecuted = 0;  // Trades executed counter
int        signalsProcessed = 0; // Signals processed counter

// Statistics per file
int        buySignals = 0;
int        sellSignals = 0;
int        exitSignals = 0;
int        holdSignals = 0;
int        skippedSignals = 0;

// Multi-file statistics
double     initialDeposit = 0;
double     totalNetProfit = 0;
int        totalTradesAllFiles = 0;

//+------------------------------------------------------------------+
//| Expert Initialization Function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   // Print startup banner
   Print("================================================================");
   Print("===   PythonSignalExecutor Multi-File EA v3.0 Starting      ===");
   Print("================================================================");
   Print("Signals Folder: ", SignalsFolder);
   Print("Folder Pattern: ", FolderPattern);
   Print("Specific File: ", SpecificFile == "" ? "None (scan folder)" : SpecificFile);
   Print("Process All Files: ", ProcessAllFiles ? "Yes" : "No");
   Print("Symbol: ", _Symbol);
   Print("Timeframe: ", EnumToString((ENUM_TIMEFRAMES)_Period));
   Print("Risk Percent: ", RiskPercent, "%");
   Print("Magic Number: ", MagicNumber);
   Print("================================================================");
   
   // Store initial deposit
   initialDeposit = AccountInfoDouble(ACCOUNT_BALANCE);
   
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
   
   // Load signal files
   if(SpecificFile != "")
   {
      // Load single specific file
      if(!LoadSingleFile(SpecificFile))
      {
         Print("ERROR: Failed to load specified file: ", SpecificFile);
         return INIT_FAILED;
      }
   }
   else
   {
      // Scan folder for matching files
      if(!ScanAndLoadFiles(FolderPattern))
      {
         Print("ERROR: Failed to load files matching pattern: ", FolderPattern);
         return INIT_FAILED;
      }
   }
   
   // Validate signals loaded
   if(totalSignals == 0)
   {
      Print("ERROR: No signals found in any files");
      return INIT_FAILED;
   }
   
   // Print load summary
   Print("================================================================");
   Print("Successfully loaded ", totalFiles, " file(s) with ", totalSignals, " total signals");
   if(totalSignals > 0)
   {
      Print("Date range: ", TimeToString(signals[0].timestamp), 
            " to ", TimeToString(signals[totalSignals-1].timestamp));
   }
   Print("Signal types: BUY=", buySignals, " SELL=", sellSignals, 
         " EXIT=", exitSignals, " HOLD=", holdSignals);
   if(skippedSignals > 0)
      Print("Skipped signals: ", skippedSignals);
   Print("================================================================");
   
   filesLoaded = true;
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert Deinitialization Function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("================================================================");
   Print("===   PythonSignalExecutor Multi-File EA Stopped            ===");
   Print("================================================================");
   Print("Deinit reason: ", reason, " - ", GetDeinitReasonText(reason));
   Print("Files processed: ", currentFileIndex, " / ", totalFiles);
   Print("Signals processed: ", signalsProcessed, " / ", totalSignals);
   Print("Total trades executed: ", tradesExecuted);
   Print("Signals skipped: ", skippedSignals);
   
   // Print performance summary
   double finalBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   double netProfit = finalBalance - initialDeposit;
   double returnPct = (netProfit / initialDeposit) * 100.0;
   
   Print("--- Performance Summary ---");
   Print("Initial Deposit: ", DoubleToString(initialDeposit, 2));
   Print("Final Balance: ", DoubleToString(finalBalance, 2));
   Print("Net Profit: ", DoubleToString(netProfit, 2));
   Print("Return: ", DoubleToString(returnPct, 2), "%");
   Print("================================================================");
}

//+------------------------------------------------------------------+
//| Expert Tick Function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Skip if files not loaded
   if(!filesLoaded || totalSignals == 0)
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
//| Scan Folder and Load All Matching Files                          |
//+------------------------------------------------------------------+
bool ScanAndLoadFiles(string pattern)
{
   // Prepend signals folder path to pattern
   string fullPattern = SignalsFolder + pattern;
   Print("Scanning folder for files matching: ", fullPattern);
   
   // Search for files
   string filename;
   long search_handle = FileFindFirst(fullPattern, filename);
   
   if(search_handle == INVALID_HANDLE)
   {
      Print("ERROR: No files found matching pattern: ", fullPattern);
      Print("Make sure signals are in: Terminal\\Common\\Files\\", SignalsFolder);
      return false;
   }
   
   // Collect all matching files
   do
   {
      if(filename != "" && StringFind(filename, ".csv") > 0)
      {
         ArrayResize(files, totalFiles + 1);
         files[totalFiles].filename = filename;
         files[totalFiles].file_date = ExtractDateFromFilename(filename);
         files[totalFiles].signal_count = 0;
         files[totalFiles].processed = false;
         totalFiles++;
         
         if(LogFileList)
            Print("Found file: ", filename);
      }
   }
   while(FileFindNext(search_handle, filename));
   
   FileFindClose(search_handle);
   
   if(totalFiles == 0)
   {
      Print("ERROR: No valid CSV files found");
      return false;
   }
   
   Print("Found ", totalFiles, " file(s)");
   
   // Sort files if requested
   if(SortByDate && totalFiles > 1)
   {
      SortFilesByDate();
      Print("Files sorted by date");
   }
   
   // Load all files
   for(int i = 0; i < totalFiles; i++)
   {
      Print("--- Loading file ", (i+1), "/", totalFiles, ": ", files[i].filename, " ---");
      
      if(!LoadSignalFile(files[i].filename, i))
      {
         Print("WARNING: Failed to load file: ", files[i].filename);
         continue;
      }
      
      files[i].processed = true;
   }
   
   return totalSignals > 0;
}

//+------------------------------------------------------------------+
//| Load Single Specific File                                         |
//+------------------------------------------------------------------+
bool LoadSingleFile(string filename)
{
   Print("Loading single file from: ", SignalsFolder + filename);
   
   ArrayResize(files, 1);
   files[0].filename = filename;
   files[0].file_date = ExtractDateFromFilename(filename);
   files[0].signal_count = 0;
   files[0].processed = false;
   totalFiles = 1;
   
   if(!LoadSignalFile(filename, 0))
   {
      Print("ERROR: Failed to load file: ", filename);
      return false;
   }
   
   files[0].processed = true;
   return totalSignals > 0;
}

//+------------------------------------------------------------------+
//| Load Signal File from CSV                                         |
//+------------------------------------------------------------------+
bool LoadSignalFile(string filename, int fileIndex)
{
   int fileSignalCount = 0;
   
   // Prepend signals folder path
   string fullPath = SignalsFolder + filename;
   
   // Open file for reading
   int fileHandle = FileOpen(fullPath, FILE_READ|FILE_CSV|FILE_ANSI, ',');
   
   if(fileHandle == INVALID_HANDLE)
   {
      Print("ERROR: Cannot open file: ", fullPath, ". Error code: ", GetLastError());
      Print("Make sure file exists in: Terminal\\Common\\Files\\", SignalsFolder);
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
         if(LogVerbose)
            Print("WARNING: Invalid timestamp at line ", lineNumber, " in ", filename, ": ", timestamp_str);
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
      signal.source_file = filename;
      
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
      fileSignalCount++;
      
      // Count signal types
      if(signal.signal == "BUY") buySignals++;
      else if(signal.signal == "SELL") sellSignals++;
      else if(signal.signal == "EXIT") exitSignals++;
      else if(signal.signal == "HOLD") holdSignals++;
   }
   
   FileClose(fileHandle);
   
   files[fileIndex].signal_count = fileSignalCount;
   
   Print("Loaded ", fileSignalCount, " signals from ", filename);
   
   return fileSignalCount > 0;
}

//+------------------------------------------------------------------+
//| Sort Files by Date                                                |
//+------------------------------------------------------------------+
void SortFilesByDate()
{
   // Simple bubble sort by file_date
   for(int i = 0; i < totalFiles - 1; i++)
   {
      for(int j = 0; j < totalFiles - i - 1; j++)
      {
         if(files[j].file_date > files[j+1].file_date)
         {
            // Swap
            FileInfo temp = files[j];
            files[j] = files[j+1];
            files[j+1] = temp;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Extract Date from Filename                                        |
//| Expected format: BT_YYYYMMDD_HHMMSS_SYMBOL_TF_signals.csv       |
//+------------------------------------------------------------------+
datetime ExtractDateFromFilename(string filename)
{
   // Try to extract date from filename pattern: BT_YYYYMMDD_HHMMSS
   int pos = StringFind(filename, "BT_");
   if(pos >= 0)
   {
      string datePart = StringSubstr(filename, pos + 3, 8); // YYYYMMDD
      string timePart = StringSubstr(filename, pos + 12, 6); // HHMMSS
      
      // Convert to datetime
      string dateTimeStr = StringSubstr(datePart, 0, 4) + "." +  // YYYY
                           StringSubstr(datePart, 4, 2) + "." +   // MM
                           StringSubstr(datePart, 6, 2) + " " +   // DD
                           StringSubstr(timePart, 0, 2) + ":" +   // HH
                           StringSubstr(timePart, 2, 2) + ":" +   // MM
                           StringSubstr(timePart, 4, 2);          // SS
      
      return StringToTime(dateTimeStr);
   }
   
   // If pattern doesn't match, return 0 (will sort to beginning)
   return 0;
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
      // Only log once per file
      static string lastWarnFile = "";
      if(signal.source_file != lastWarnFile)
      {
         Print("WARNING: Signal symbol (", signal.symbol, ") differs from EA symbol (", _Symbol, ")");
         lastWarnFile = signal.source_file;
      }
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Process Signals for Current Bar                                   |
//+------------------------------------------------------------------+
void ProcessSignalsForBar(datetime bar_time)
{
   string currentFile = "";
   
   // Search for signals matching this bar time
   for(int i = currentSignalIndex; i < totalSignals; i++)
   {
      // Track file transitions
      if(signals[i].source_file != currentFile && currentFile != "")
      {
         Print("--- Transitioned to file: ", signals[i].source_file, " ---");
         
         // Reset equity if requested
         if(ResetEquityBetweenFiles)
         {
            Print("Resetting equity to initial deposit");
            // Close all positions
            CloseAllPositions();
            // In real trading, you'd need to adjust account balance here
            // In strategy tester, this is just informational
         }
      }
      currentFile = signals[i].source_file;
      
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
            Print("WARNING: Skipped past signal at ", TimeToString(signals[i].timestamp), 
                  " from ", signals[i].source_file);
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
      Print("File: ", signal.source_file);
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
      double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
      double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
      double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
      
      // Simple risk-based calculation
      lotSize = riskAmount / (tickValue * 100);
      
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
      lotSize = minLot;
   if(lotSize > maxLot)
      lotSize = maxLot;
   
   return lotSize;
}

//+------------------------------------------------------------------+
//| Open Position                                                     |
//+------------------------------------------------------------------+
bool OpenPosition(ENUM_ORDER_TYPE orderType, double lotSize, double stopLoss, double takeProfit, string comment)
{
   double price = 0;
   if(orderType == ORDER_TYPE_BUY)
      price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   else
      price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   double sl = NormalizePrice(stopLoss);
   double tp = NormalizePrice(takeProfit);
   
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
   request.comment = StringSubstr(comment, 0, 31);
   request.type_filling = ORDER_FILLING_FOK;
   
   if(!OrderSend(request, result))
   {
      request.type_filling = ORDER_FILLING_IOC;
      if(!OrderSend(request, result))
      {
         request.type_filling = ORDER_FILLING_RETURN;
         OrderSend(request, result);
      }
   }
   
   if(result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED)
   {
      Print("✓ ", (orderType == ORDER_TYPE_BUY ? "LONG" : "SHORT"), 
            " position opened: ", lotSize, " lots at ", DoubleToString(price, _Digits),
            " | Ticket: ", result.order);
      return true;
   }
   else
   {
      Print("✗ Failed to open position. Error: ", result.retcode);
      return false;
   }
}

//+------------------------------------------------------------------+
//| Close Current Position                                            |
//+------------------------------------------------------------------+
bool ClosePosition()
{
   if(!PositionSelect(_Symbol))
      return false;
   
   long ticket = PositionGetInteger(POSITION_TICKET);
   double volume = PositionGetDouble(POSITION_VOLUME);
   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   
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
   
   if(!OrderSend(request, result))
   {
      request.type_filling = ORDER_FILLING_IOC;
      if(!OrderSend(request, result))
      {
         request.type_filling = ORDER_FILLING_RETURN;
         OrderSend(request, result);
      }
   }
   
   if(result.retcode == TRADE_RETCODE_DONE)
   {
      double profit = PositionGetDouble(POSITION_PROFIT);
      Print("✓ Position closed: ", volume, " lots | Profit: ", DoubleToString(profit, 2));
      return true;
   }
   
   return false;
}

//+------------------------------------------------------------------+
//| Close All Positions                                               |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) == _Symbol)
      {
         long ticket = PositionGetInteger(POSITION_TICKET);
         if(PositionSelectByTicket(ticket))
            ClosePosition();
      }
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
