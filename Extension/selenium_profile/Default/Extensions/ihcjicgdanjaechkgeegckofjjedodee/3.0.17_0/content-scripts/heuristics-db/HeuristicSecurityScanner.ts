import { browserName, domain } from "@/utils/utils";
import {BlockURL, RuleType} from "@/content-scripts/heuristics-db/types";
import { onScam, RecordType } from "@/app/scripts/app";
import { chrome } from "@/utils/polyfill";
import { sha256 } from "js-sha256";
import { simpleStorageSet } from "@/utils/storage";



const threatNamePrefix = {
  heuristic: "heuristic_",
};

class HeuristicSecurityScanner {
  private readonly malwarebytes: any; // Replace with proper type if available
  private readonly isSafari: boolean; // Replace with proper type if available

  constructor(malwarebytesInstance: any) {
    this.malwarebytes = malwarebytesInstance;
    this.isSafari = browserName() === "Safari";
  }

  /**
   * Update security metrics and badge count
   */
  private async updateSecurityMetrics(
    tabId: number,
    tabUrl: string,
    requestDomain: string
  ): Promise<void> {
    await this.malwarebytes.recordAll(
      RecordType.SCAM,
      tabId,
      domain(tabUrl),
      requestDomain,
      true
    );
    await this.malwarebytes.updateBadgeCount(tabId);
    await simpleStorageSet({ lastDBused: null });
  }

  /**
   * Determines whether a given domain should be excluded based on the threat type and mode.
   *
   * @param sourceDomain - The domain to check for exclusion.
   * @param isAggressiveMode - A boolean indicating if the aggressive mode is enabled.
   * @param threatType - The type of threat to check against.
   * @returns A boolean indicating whether the domain should be excluded.
   * Return true if the domain should be excluded, false otherwise.
   */
  private shouldExcludeDomain(
    sourceDomain: string,
    isAggressiveMode: boolean,
    threatType: RuleType
  ): boolean {
    if (threatType === RuleType.SCAM || threatType === RuleType.PHISHING) {
      let whitelisted = this.malwarebytes.isWhitelisted(
        sourceDomain,
        this.malwarebytes.DATABASES.whitelist_scams_manual,
        "Scams"
      ) || 
      this.malwarebytes.isWhitelistedScamsByPattern(sourceDomain) ||
      (!isAggressiveMode && 
        this.malwarebytes.isWhitelisted(
          sourceDomain,
          this.malwarebytes.DATABASES.top1m,
          "Scams"
        ));
      
      return whitelisted;
    }
    return false;
  }

  /**
   * Main scan method to detect threats
   */
  public async scanForThreats(
    urlsToBlock: BlockURL[],
    sourceUrl: string,
    tabId: number
  ): Promise<void> {
    const sourceDomain = domain(sourceUrl);

    urlsToBlock.forEach(
      ({ domain, isSilent, type: threatType, isAggressiveMode, source, id }) => {
        const isAdProtectionActive = this.malwarebytes.isProtectionActive(
          "EXCLUSION_ADS",
          sourceUrl,
          tabId
        );
        if (!isAdProtectionActive) {
          return;
        }

      if (!sourceUrl.includes(domain)) return null;
        if (this.shouldExcludeDomain(sourceDomain, Boolean(isAggressiveMode), threatType)) {
          return null;
        }

      const subtype = `${threatType}_heuristic`;
      const blockMessage = `BTW: (NETWORK_BLOCK) heuristic ${threatType} domain found on ${sourceDomain}`;

      this.updateSecurityMetrics(tabId, sourceUrl, sourceDomain);

      //@ts-ignore
      const action = onScam({
        tabId: tabId,
        tabURL: sourceUrl,
        url: sourceDomain,
        type: threatType,
        subtype,
        rule: `${threatNamePrefix.heuristic}${id}`,
        blockMessage,
        isSilent,
        selectedCheckedDBs:
          threatType === RuleType.SCAM
            ? [this.malwarebytes.DATABASES.heuristics]
            : undefined,
      });
      chrome.tabs.update(tabId, { url: action.redirectUrl });
    });
  }
}

export { HeuristicSecurityScanner };
