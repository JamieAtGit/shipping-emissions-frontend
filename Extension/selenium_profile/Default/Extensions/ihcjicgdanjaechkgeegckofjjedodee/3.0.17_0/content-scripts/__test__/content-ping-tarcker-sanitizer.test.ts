import { getCurrentTabId, removePingAttributes, handlePingSanitizer } from '../content-ping-tarcker-sanitizer';
import { recordPingTrackerRemoval } from '@/content-scripts/common-utils';

jest.mock('@/content-scripts/common-utils', () => ({
    recordPingTrackerRemoval: jest.fn(),
}));

jest.mock('@/app/scripts/ui-utils/ui-utils.js', () => ({
    settingsGetAsync: jest.fn(),
}));

jest.mock('@/utils/polyfill', () => ({
    chrome: {
      runtime: {
        sendMessage: jest.fn(),
        lastError: null,
      },
      storage: {
        local: {
          get: jest.fn(),
        },
      },
    },
}));

describe('getCurrentTabId', () => {
    beforeEach(() => {
    });

    it('should resolve with tabId when response is received', async () => {
        (chrome.runtime.sendMessage as jest.Mock).mockImplementation((_, callback) => {
            callback({ tabId: 123 });
        });
    
        await expect(getCurrentTabId()).resolves.toEqual({ tabId: 123 });
    });

    it('should reject with an error when no response is received', async () => {
        (chrome.runtime.sendMessage as jest.Mock).mockImplementation((_, callback) => callback(null));
        await expect(getCurrentTabId()).rejects.toThrow("Error getting tab info");
    });
});

describe('removePingAttributes', () => {
    beforeEach(() => {
        document.body.innerHTML = '<a href="#" ping="https://tracker.com"></a>';
    });

    it('should remove ping attribute from anchor elements and call recordPingTrackerRemoval', () => {
        const tabId = 123;
        const pageUrl = 'example.com';
        const removedLinks = removePingAttributes(tabId, pageUrl);

        expect(removedLinks.length).toBe(1);
        expect(removedLinks[0].hasAttribute('ping')).toBe(false);
        expect(recordPingTrackerRemoval).toHaveBeenCalledWith(tabId, pageUrl);
    });
});

describe('handlePingSanitizer', () => {
    beforeEach(() => {
        document.body.innerHTML = '<a href="#" ping="https://tracker.com"></a>';
        jest.clearAllMocks();
    });

    it('should remove ping attributes on DOMContentLoaded', () => {
        const tabId = 123;
        const pageUrl = 'example.com';
        handlePingSanitizer(tabId, pageUrl);

        expect(document.querySelectorAll('a[ping]').length).toBe(0);
        expect(recordPingTrackerRemoval).toHaveBeenCalledWith(tabId, pageUrl);
    });
});
