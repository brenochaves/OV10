const OV10_DEBUG_BRIDGE = Object.freeze({
  defaultSpreadsheetId: '1k4YS0jQRMzDVp34DLL8Yhb8rgM_89pGqcP-JABLRO7U',
  remoteKey: '8hfD4R5mfG',
  remoteBaseUrl: 'https://sistema.dlombelloplanilhas.com/scripts.php',
  sharedAccessKey: 'ov10-bridge-20260312-b8d1f0f6',
  defaultChunkLength: 12000,
  defaultPreviewRows: 20,
  defaultPreviewCols: 12,
});

function dbgPing() {
  return dbgOk_({
    timestampUtc: new Date().toISOString(),
    scriptId: ScriptApp.getScriptId(),
    activeUserEmail: Session.getActiveUser().getEmail() || null,
    defaultSpreadsheetId: OV10_DEBUG_BRIDGE.defaultSpreadsheetId,
  });
}

function dbgListSheets(spreadsheetId) {
  const spreadsheet = openSpreadsheet_(spreadsheetId);
  const sheets = spreadsheet.getSheets().map(function (sheet) {
    return {
      name: sheet.getName(),
      sheetId: sheet.getSheetId(),
      hidden: sheet.isSheetHidden(),
      maxRows: sheet.getMaxRows(),
      maxColumns: sheet.getMaxColumns(),
      lastRow: sheet.getLastRow(),
      lastColumn: sheet.getLastColumn(),
      frozenRows: sheet.getFrozenRows(),
      frozenColumns: sheet.getFrozenColumns(),
    };
  });
  return dbgOk_({
    spreadsheetId: spreadsheet.getId(),
    spreadsheetName: spreadsheet.getName(),
    spreadsheetUrl: spreadsheet.getUrl(),
    sheetCount: sheets.length,
    sheets: sheets,
  });
}

function dbgListNamedRanges(spreadsheetId) {
  const spreadsheet = openSpreadsheet_(spreadsheetId);
  const namedRanges = spreadsheet.getNamedRanges().map(function (namedRange) {
    const range = namedRange.getRange();
    return {
      name: namedRange.getName(),
      sheetName: range.getSheet().getName(),
      a1Notation: range.getA1Notation(),
    };
  });
  return dbgOk_({
    spreadsheetId: spreadsheet.getId(),
    namedRangeCount: namedRanges.length,
    namedRanges: namedRanges,
  });
}

function dbgReadRange(spreadsheetId, sheetName, a1Notation) {
  const range = resolveRange_(spreadsheetId, sheetName, a1Notation);
  return dbgOk_({
    spreadsheetId: range.getSheet().getParent().getId(),
    sheetName: range.getSheet().getName(),
    a1Notation: range.getA1Notation(),
    rowCount: range.getNumRows(),
    columnCount: range.getNumColumns(),
    values: range.getValues(),
    displayValues: range.getDisplayValues(),
    formulas: range.getFormulas(),
    notes: range.getNotes(),
  });
}

function dbgSheetPreview(spreadsheetId, sheetName, maxRows, maxColumns) {
  const spreadsheet = openSpreadsheet_(spreadsheetId);
  const sheet = getSheetRequired_(spreadsheet, sheetName);
  const previewRows = normalizePositiveInt_(maxRows, OV10_DEBUG_BRIDGE.defaultPreviewRows);
  const previewColumns = normalizePositiveInt_(
    maxColumns,
    OV10_DEBUG_BRIDGE.defaultPreviewCols
  );
  const totalRows = Math.max(sheet.getLastRow(), 1);
  const totalColumns = Math.max(sheet.getLastColumn(), 1);
  const rows = Math.min(previewRows, totalRows);
  const columns = Math.min(previewColumns, totalColumns);
  const range = sheet.getRange(1, 1, rows, columns);
  return dbgOk_({
    spreadsheetId: spreadsheet.getId(),
    spreadsheetName: spreadsheet.getName(),
    sheetName: sheet.getName(),
    requestedRows: previewRows,
    requestedColumns: previewColumns,
    returnedRows: rows,
    returnedColumns: columns,
    totalRows: totalRows,
    totalColumns: totalColumns,
    values: range.getValues(),
    displayValues: range.getDisplayValues(),
    formulas: range.getFormulas(),
  });
}

function dbgWorkbookVersion(spreadsheetId) {
  const spreadsheet = openSpreadsheet_(spreadsheetId);
  const readmeSheet = getSheetRequired_(spreadsheet, 'LeiaMe');
  const versionLabel = String(readmeSheet.getRange('B6').getDisplayValue()).trim();
  if (!versionLabel) {
    throw new Error('LeiaMe!B6 is empty.');
  }
  const normalizedVersion = versionLabel.replace(/^v/i, '');
  const parts = normalizedVersion.split('.');
  if (parts.length < 2) {
    throw new Error('Unexpected workbook version format: ' + versionLabel);
  }
  const remoteScriptVersion = 'v61_controle_' + parts[0] + parts[1];
  return dbgOk_({
    spreadsheetId: spreadsheet.getId(),
    spreadsheetName: spreadsheet.getName(),
    versionCell: 'LeiaMe!B6',
    workbookVersionLabel: versionLabel,
    remoteScriptVersion: remoteScriptVersion,
    remoteUrl: buildRemoteScriptUrl_(remoteScriptVersion),
  });
}

function dbgFetchRemoteScriptSummary(spreadsheetId) {
  const payload = fetchRemoteScript_(spreadsheetId);
  return dbgOk_({
    spreadsheetId: resolveSpreadsheetId_(spreadsheetId),
    workbookVersionLabel: payload.workbookVersionLabel,
    remoteScriptVersion: payload.remoteScriptVersion,
    remoteUrl: payload.remoteUrl,
    responseCode: payload.responseCode,
    fetchedAtUtc: payload.fetchedAtUtc,
    contentLength: payload.content.length,
    sha256Hex: payload.sha256Hex,
    contentType: payload.contentType,
    previewStart: payload.content.slice(0, 240),
    previewEnd: payload.content.slice(-240),
  });
}

function dbgFetchRemoteScriptChunk(spreadsheetId, start, length) {
  const payload = fetchRemoteScript_(spreadsheetId);
  const chunkStart = Math.max(0, normalizePositiveInt_(start, 0));
  const chunkLength = normalizePositiveInt_(length, OV10_DEBUG_BRIDGE.defaultChunkLength);
  const chunkEnd = Math.min(payload.content.length, chunkStart + chunkLength);
  return dbgOk_({
    spreadsheetId: resolveSpreadsheetId_(spreadsheetId),
    workbookVersionLabel: payload.workbookVersionLabel,
    remoteScriptVersion: payload.remoteScriptVersion,
    remoteUrl: payload.remoteUrl,
    responseCode: payload.responseCode,
    fetchedAtUtc: payload.fetchedAtUtc,
    start: chunkStart,
    endExclusive: chunkEnd,
    totalLength: payload.content.length,
    chunkLength: chunkEnd - chunkStart,
    sha256Hex: payload.sha256Hex,
    content: payload.content.slice(chunkStart, chunkEnd),
  });
}

function dbgCreateDebugCopy(sourceSpreadsheetId, copyNamePrefix) {
  const sourceId = resolveSpreadsheetId_(sourceSpreadsheetId);
  const sourceFile = DriveApp.getFileById(sourceId);
  const prefix = String(copyNamePrefix || 'OV10 Debug Copy').trim();
  const timestamp = Utilities.formatDate(
    new Date(),
    Session.getScriptTimeZone(),
    "yyyy-MM-dd'_'HHmmss"
  );
  const copyName = prefix + ' - ' + sourceFile.getName() + ' - ' + timestamp;
  const copiedFile = sourceFile.makeCopy(copyName);
  const spreadsheet = SpreadsheetApp.openById(copiedFile.getId());
  return dbgOk_({
    sourceSpreadsheetId: sourceId,
    sourceName: sourceFile.getName(),
    copiedSpreadsheetId: copiedFile.getId(),
    copiedName: copiedFile.getName(),
    copiedUrl: spreadsheet.getUrl(),
    note:
      'Google Sheets copies the bound Apps Script with the spreadsheet. Open Extensions > Apps Script in the copied sheet if bound-script instrumentation becomes necessary.',
  });
}

function dbgDescribeProtections(spreadsheetId) {
  const spreadsheet = openSpreadsheet_(spreadsheetId);
  const sheets = spreadsheet.getSheets().map(function (sheet) {
    const sheetProtections = sheet
      .getProtections(SpreadsheetApp.ProtectionType.SHEET)
      .map(serializeProtection_);
    const rangeProtections = sheet
      .getProtections(SpreadsheetApp.ProtectionType.RANGE)
      .map(serializeProtection_);
    return {
      name: sheet.getName(),
      sheetProtections: sheetProtections,
      rangeProtections: rangeProtections,
    };
  });
  return dbgOk_({
    spreadsheetId: spreadsheet.getId(),
    spreadsheetName: spreadsheet.getName(),
    sheets: sheets,
  });
}

function dbgBridgeState() {
  return dbgOk_({
    scriptProperties: PropertiesService.getScriptProperties().getProperties(),
    triggerCount: ScriptApp.getProjectTriggers().length,
    triggers: ScriptApp.getProjectTriggers().map(function (trigger) {
      return {
        handlerFunction: trigger.getHandlerFunction(),
        eventType: String(trigger.getEventType()),
        triggerSource: String(trigger.getTriggerSource()),
      };
    }),
  });
}

function dbgDispatch(request) {
  const op = String((request && request.operation) || '').trim();
  if (!op) {
    throw new Error('Missing operation.');
  }
  switch (op) {
    case 'ping':
      return dbgPing();
    case 'listSheets':
      return dbgListSheets(request.spreadsheetId);
    case 'listNamedRanges':
      return dbgListNamedRanges(request.spreadsheetId);
    case 'readRange':
      return dbgReadRange(request.spreadsheetId, request.sheetName, request.a1Notation);
    case 'sheetPreview':
      return dbgSheetPreview(
        request.spreadsheetId,
        request.sheetName,
        request.maxRows,
        request.maxColumns
      );
    case 'workbookVersion':
      return dbgWorkbookVersion(request.spreadsheetId);
    case 'fetchRemoteScriptSummary':
      return dbgFetchRemoteScriptSummary(request.spreadsheetId);
    case 'fetchRemoteScriptChunk':
      return dbgFetchRemoteScriptChunk(request.spreadsheetId, request.start, request.length);
    case 'createDebugCopy':
      return dbgCreateDebugCopy(request.spreadsheetId, request.copyNamePrefix);
    case 'describeProtections':
      return dbgDescribeProtections(request.spreadsheetId);
    case 'bridgeState':
      return dbgBridgeState();
    default:
      throw new Error('Unsupported operation: ' + op);
  }
}

function doGet(e) {
  requireBridgeKey_(normalizeGetRequest_(e));
  return jsonOutput_(safeDispatch_(normalizeGetRequest_(e)));
}

function doPost(e) {
  const normalizedRequest = normalizePostRequest_(e);
  requireBridgeKey_(normalizedRequest);
  return jsonOutput_(
    safeDispatch_(function () {
      return normalizedRequest;
    })
  );
}

function safeDispatch_(request) {
  try {
    const normalizedRequest = typeof request === 'function' ? request() : request;
    return dbgDispatch(normalizedRequest);
  } catch (error) {
    return {
      ok: false,
      error: {
        message: error && error.message ? error.message : String(error),
        stack: error && error.stack ? String(error.stack) : null,
      },
      request: typeof request === 'function' ? null : request || null,
      timestampUtc: new Date().toISOString(),
    };
  }
}

function normalizeGetRequest_(event) {
  const parameters = (event && event.parameter) || {};
  return {
    operation: parameters.operation || parameters.op,
    bridgeKey: parameters.bridgeKey,
    spreadsheetId: parameters.spreadsheetId,
    sheetName: parameters.sheetName,
    a1Notation: parameters.a1Notation,
    maxRows: parameters.maxRows,
    maxColumns: parameters.maxColumns,
    start: parameters.start,
    length: parameters.length,
    copyNamePrefix: parameters.copyNamePrefix,
  };
}

function normalizePostRequest_(event) {
  if (!event || !event.postData || !event.postData.contents) {
    return {};
  }
  return JSON.parse(event.postData.contents);
}

function requireBridgeKey_(request) {
  const providedKey = String((request && request.bridgeKey) || '').trim();
  if (!providedKey || providedKey !== OV10_DEBUG_BRIDGE.sharedAccessKey) {
    throw new Error('Invalid bridgeKey.');
  }
}

function fetchRemoteScript_(spreadsheetId) {
  const versionInfo = dbgWorkbookVersion(spreadsheetId).data;
  const response = UrlFetchApp.fetch(versionInfo.remoteUrl, {
    followRedirects: true,
    muteHttpExceptions: true,
  });
  const content = response.getContentText();
  return {
    workbookVersionLabel: versionInfo.workbookVersionLabel,
    remoteScriptVersion: versionInfo.remoteScriptVersion,
    remoteUrl: versionInfo.remoteUrl,
    responseCode: response.getResponseCode(),
    contentType: response.getAllHeaders()['Content-Type'] || null,
    fetchedAtUtc: new Date().toISOString(),
    content: content,
    sha256Hex: sha256Hex_(content),
  };
}

function buildRemoteScriptUrl_(remoteScriptVersion) {
  return (
    OV10_DEBUG_BRIDGE.remoteBaseUrl +
    '?key=' +
    OV10_DEBUG_BRIDGE.remoteKey +
    '&file=' +
    encodeURIComponent(remoteScriptVersion)
  );
}

function resolveRange_(spreadsheetId, sheetName, a1Notation) {
  const spreadsheet = openSpreadsheet_(spreadsheetId);
  const sheet = getSheetRequired_(spreadsheet, sheetName);
  const notation = String(a1Notation || '').trim();
  if (!notation) {
    throw new Error('Missing a1Notation.');
  }
  return sheet.getRange(notation);
}

function openSpreadsheet_(spreadsheetId) {
  return SpreadsheetApp.openById(resolveSpreadsheetId_(spreadsheetId));
}

function resolveSpreadsheetId_(spreadsheetId) {
  const resolved = String(spreadsheetId || OV10_DEBUG_BRIDGE.defaultSpreadsheetId).trim();
  if (!resolved) {
    throw new Error('Missing spreadsheetId.');
  }
  return resolved;
}

function getSheetRequired_(spreadsheet, sheetName) {
  const name = String(sheetName || '').trim();
  if (!name) {
    throw new Error('Missing sheetName.');
  }
  const sheet = spreadsheet.getSheetByName(name);
  if (!sheet) {
    throw new Error('Sheet not found: ' + name);
  }
  return sheet;
}

function normalizePositiveInt_(value, fallbackValue) {
  if (value === 0 || value === '0') {
    return 0;
  }
  const parsed = parseInt(value, 10);
  if (isNaN(parsed) || parsed < 0) {
    return fallbackValue;
  }
  return parsed;
}

function serializeProtection_(protection) {
  let rangeA1Notation = null;
  try {
    rangeA1Notation = protection.getRange().getA1Notation();
  } catch (error) {
    rangeA1Notation = null;
  }
  return {
    description: protection.getDescription() || null,
    type: String(protection.getProtectionType()),
    editors: protection
      .getEditors()
      .map(function (editor) {
        return editor.getEmail();
      })
      .filter(Boolean),
    domainEdit: protection.canDomainEdit(),
    unprotectedRangesCount: protection.getUnprotectedRanges().length,
    rangeA1Notation: rangeA1Notation,
  };
}

function sha256Hex_(content) {
  const digest = Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    content,
    Utilities.Charset.UTF_8
  );
  return digest
    .map(function (byte) {
      const normalized = byte < 0 ? byte + 256 : byte;
      return ('0' + normalized.toString(16)).slice(-2);
    })
    .join('');
}

function dbgOk_(data) {
  return {
    ok: true,
    timestampUtc: new Date().toISOString(),
    data: data,
  };
}

function jsonOutput_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload, null, 2)).setMimeType(
    ContentService.MimeType.JSON
  );
}
