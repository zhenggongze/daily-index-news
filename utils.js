const fs = require('fs');
const path = require('path');

function getShanghaiDate() {
    const now = new Date();
    const formatter = new Intl.DateTimeFormat('zh-CN', {
        timeZone: 'Asia/Shanghai',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
    const parts = formatter.formatToParts(now);
    const year = parts.find(p => p.type === 'year').value;
    const month = parts.find(p => p.type === 'month').value;
    const day = parts.find(p => p.type === 'day').value;
    return `${year}-${month}-${day}`;
}

function getShanghaiDateStr() {
    const now = new Date();
    const formatter = new Intl.DateTimeFormat('zh-CN', {
        timeZone: 'Asia/Shanghai',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    return formatter.format(now);
}

function getShanghaiWeekday() {
    const now = new Date();
    const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
    const formatter = new Intl.DateTimeFormat('zh-CN', {
        timeZone: 'Asia/Shanghai',
        weekday: 'long'
    });
    const weekNum = now.getDay();
    return weekdays[weekNum];
}

function isWeekend() {
    const now = new Date();
    const formatter = new Intl.DateTimeFormat('zh-CN', {
        timeZone: 'Asia/Shanghai',
        weekday: 'long'
    });
    const weekNum = now.getDay();
    return weekNum === 0 || weekNum === 6;
}

function atomicWriteFile(filePath, content, encoding = 'utf8') {
    return new Promise((resolve, reject) => {
        const tmpPath = filePath + '.tmp';
        let attempts = 0;
        const maxAttempts = 3;
        
        function write() {
            attempts++;
            fs.writeFile(tmpPath, content, encoding, (err) => {
                if (err) {
                    if (attempts < maxAttempts) {
                        setTimeout(write, 1000);
                    } else {
                        reject(err);
                    }
                    return;
                }
                fs.rename(tmpPath, filePath, (renameErr) => {
                    if (renameErr) {
                        fs.unlink(tmpPath, () => {});
                        if (attempts < maxAttempts) {
                            setTimeout(write, 1000);
                        } else {
                            reject(renameErr);
                        }
                    } else {
                        resolve();
                    }
                });
            });
        }
        write();
    });
}

function atomicWriteFileSync(filePath, content, encoding = 'utf8') {
    const tmpPath = filePath + '.tmp';
    for (let attempts = 0; attempts < 3; attempts++) {
        try {
            fs.writeFileSync(tmpPath, content, encoding);
            fs.renameSync(tmpPath, filePath);
            return true;
        } catch (e) {
            try { fs.unlinkSync(tmpPath); } catch (e2) {}
            if (attempts < 2) {
                const start = Date.now();
                while (Date.now() - start < 1000) {}
            }
        }
    }
    return false;
}

function readJsonWithBackup(filePath, defaultValue = {}) {
    const bakPath = filePath + '.bak';
    try {
        const content = fs.readFileSync(filePath, 'utf8');
        return JSON.parse(content);
    } catch (e) {
        try {
            const bakContent = fs.readFileSync(bakPath, 'utf8');
            return JSON.parse(bakContent);
        } catch (e2) {
            return defaultValue;
        }
    }
}

function writeJsonWithBackup(filePath, data, encoding = 'utf8') {
    const bakPath = filePath + '.bak';
    try {
        fs.copyFileSync(filePath, bakPath);
    } catch (e) {}
    
    const content = JSON.stringify(data, null, 2);
    return atomicWriteFileSync(filePath, content, encoding);
}

function cleanupOldFiles(dirPath, prefix, daysToKeep = 3) {
    try {
        const files = fs.readdirSync(dirPath);
        const now = Date.now();
        const cutoff = now - daysToKeep * 24 * 60 * 60 * 1000;
        
        for (const file of files) {
            if (file.startsWith(prefix)) {
                const filePath = path.join(dirPath, file);
                try {
                    const stats = fs.statSync(filePath);
                    if (stats.mtime.getTime() < cutoff) {
                        fs.unlinkSync(filePath);
                    }
                } catch (e) {}
            }
        }
    } catch (e) {}
}

const LOCK_TIMEOUT = 30 * 60 * 1000;

function getLock(lockPath) {
    try {
        if (fs.existsSync(lockPath)) {
            const lockContent = fs.readFileSync(lockPath, 'utf8');
            const lockData = JSON.parse(lockContent);
            if (Date.now() - lockData.timestamp < LOCK_TIMEOUT) {
                return false;
            }
        }
        const lockData = {
            timestamp: Date.now(),
            pid: process.pid
        };
        fs.writeFileSync(lockPath, JSON.stringify(lockData));
        return true;
    } catch (e) {
        return false;
    }
}

function releaseLock(lockPath) {
    try {
        fs.unlinkSync(lockPath);
    } catch (e) {}
}

function logExecution(logPath, step, status, details = '') {
    try {
        let logs = [];
        if (fs.existsSync(logPath)) {
            const content = fs.readFileSync(logPath, 'utf8');
            logs = JSON.parse(content);
        }
        
        const logEntry = {
            timestamp: new Date().toISOString(),
            shanghaiTime: new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }),
            step,
            status,
            details
        };
        
        logs.push(logEntry);
        if (logs.length > 100) {
            logs = logs.slice(-100);
        }
        
        atomicWriteFileSync(logPath, JSON.stringify(logs, null, 2));
    } catch (e) {}
}

function getStatusFromMultipleSources(baseDir) {
    const statusPath = path.join(baseDir, 'push_status.json');
    const reportPath = path.join(baseDir, 'today_report.md');
    const logPath = path.join(baseDir, 'push_log.json');
    
    const today = getShanghaiDate();
    let statusFromJson = false;
    let statusFromReport = false;
    let statusFromLog = false;
    
    try {
        const statusJson = JSON.parse(fs.readFileSync(statusPath, 'utf8'));
        statusFromJson = statusJson.lastSuccessDate === today;
    } catch (e) {}
    
    try {
        const reportContent = fs.readFileSync(reportPath, 'utf8');
        const dateMatch = reportContent.match(/📅\s*(\d{4})年(\d{1,2})月(\d{1,2})日/);
        if (dateMatch) {
            const reportDate = `${dateMatch[1]}-${String(dateMatch[2]).padStart(2, '0')}-${String(dateMatch[3]).padStart(2, '0')}`;
            statusFromReport = reportDate === today;
        }
    } catch (e) {}
    
    try {
        const logs = JSON.parse(fs.readFileSync(logPath, 'utf8'));
        const lastSuccess = logs.slice().reverse().find(l => l.status === 'success' && l.step === 'push');
        if (lastSuccess) {
            const logDate = lastSuccess.shanghaiTime.split(' ')[0].replace(/\//g, '-');
            statusFromLog = logDate === today;
        }
    } catch (e) {}
    
    return {
        today,
        fromJson: statusFromJson,
        fromReport: statusFromReport,
        fromLog: statusFromLog,
        needsRetry: !statusFromJson && !statusFromReport && !statusFromLog
    };
}

function getRetryCount(logPath, today) {
    try {
        const logs = JSON.parse(fs.readFileSync(logPath, 'utf8'));
        const todayLogs = logs.filter(l => {
            const logDate = l.shanghaiTime.split(' ')[0].replace(/\//g, '-');
            return logDate === today && l.step === 'push' && l.status === 'failed';
        });
        return todayLogs.length;
    } catch (e) {
        return 0;
    }
}

function shouldRetry(logPath, today) {
    const retryCount = getRetryCount(logPath, today);
    if (retryCount >= 4) return false;
    return true;
}

module.exports = {
    getShanghaiDate,
    getShanghaiDateStr,
    getShanghaiWeekday,
    isWeekend,
    atomicWriteFile,
    atomicWriteFileSync,
    readJsonWithBackup,
    writeJsonWithBackup,
    cleanupOldFiles,
    getLock,
    releaseLock,
    logExecution,
    getStatusFromMultipleSources,
    getRetryCount,
    shouldRetry
};
