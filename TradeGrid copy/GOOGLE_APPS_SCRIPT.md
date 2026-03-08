
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const action = data.action;
    
    switch(action) {
      case 'updateGrid':
        return updateExecutionGrid(data.data);
      case 'updatePricesOnly':
        return updateLivePrices(data.prices);
      default:
        return createResponse('error', 'Unknown action: ' + action);
    }
  } catch (error) {
    Logger.log('Error in doPost: ' + error.toString());
    return createResponse('error', 'Script error: ' + error.toString());
  }
}

function updateExecutionGrid(matrixData) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Execution');
    if (!sheet) {
      return createResponse('error', 'Execution sheet not found');
    }
    
    // Clear from row 1 (Login status + Portfolio grid)
    const lastRow = sheet.getLastRow();
    if (lastRow >= 1) {
      sheet.getRange(1, 1, lastRow, sheet.getLastColumn()).clearContent();
    }
    
    // Write full grid starting at row 1 (row 1 = Login/Auth Status, row 2 = Portfolio/Account, row 3 = Scrips/HOLDINGS/Price, then data)
    if (matrixData && matrixData.length > 0) {
      sheet.getRange(1, 1, matrixData.length, matrixData[0].length).setValues(matrixData);
    }
    
    return createResponse('success', 'Grid updated successfully');
  } catch (error) {
    Logger.log('Error updating grid: ' + error.toString());
    return createResponse('error', 'Grid update failed: ' + error.toString());
  }
}

function updateLivePrices(priceData) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Execution');
    if (!sheet) {
      return createResponse('error', 'Execution sheet not found');
    }
    
    const dataRange = sheet.getDataRange();
    const values = dataRange.getValues();
    const startRow = dataRange.getRow(); // 1-based
    
    // Find header row: Portfolio layout has "Scrips", "HOLDINGS", "Price" (or legacy "Symbol", "LTP")
    var headerRowIndex = -1;
    var symbolCol = -1;
    var priceCol = -1;
    for (var r = 0; r < Math.min(values.length, 10); r++) {
      var row = values[r];
      var symIdx = row.findIndex(function(h) {
        var s = (h && h.toString().toLowerCase()) || '';
        return s.indexOf('holdings') !== -1 || s.indexOf('symbol') !== -1 || s.indexOf('scrips') !== -1;
      });
      var prIdx = row.findIndex(function(h) {
        var s = (h && h.toString().toLowerCase()) || '';
        return s.indexOf('price') !== -1 || s.indexOf('ltp') !== -1;
      });
      if (symIdx !== -1 && prIdx !== -1) {
        headerRowIndex = r;
        symbolCol = symIdx;
        priceCol = prIdx;
        break;
      }
    }
    
    if (headerRowIndex === -1 || symbolCol === -1 || priceCol === -1) {
      return createResponse('error', 'Symbol or Price columns not found');
    }
    
    function getPrice(sym) {
      var s = (sym && sym.toString().trim()) || '';
      if (!s) return null;
      if (priceData[s] != null) return priceData[s];
      if (s.indexOf('-E') === s.length - 2 && priceData[s.slice(0, -2) + '-EQ'] != null) return priceData[s.slice(0, -2) + '-EQ'];
      if (s.indexOf('-EQ') === s.length - 3 && priceData[s.slice(0, -3) + '-E'] != null) return priceData[s.slice(0, -3) + '-E'];
      return null;
    }
    
    var skipLabels = ['total', 'ledger', 'positions', 'total value', ''];
    var updatedCount = 0;
    for (var i = headerRowIndex + 1; i < values.length; i++) {
      var symbol = values[i][symbolCol];
      var s = (symbol && symbol.toString().trim().toLowerCase()) || '';
      if (!s || skipLabels.indexOf(s) !== -1) continue;
      var price = getPrice(symbol);
      if (price != null) {
        sheet.getRange(startRow + i, priceCol + 1).setValue(price);
        updatedCount++;
      }
    }
    
    return createResponse('success', 'Updated ' + updatedCount + ' prices');
  } catch (error) {
    Logger.log('Error updating prices: ' + error.toString());
    return createResponse('error', 'Price update failed: ' + error.toString());
  }
}

function createResponse(status, message) {
  return ContentService.createTextOutput(JSON.stringify({
    status: status,
    message: message
  })).setMimeType(ContentService.MimeType.JSON);
}

// Helper function for testing
function testWebApp() {
  const testData = {
    action: 'updatePricesOnly',
    prices: {
      'RELIANCE': 2500.50,
      'TCS': 3400.25
    }
  };
  
  const result = doPost({
    postData: {
      contents: JSON.stringify(testData)
    }
  });
  
  Logger.log(result.getContent());
}
