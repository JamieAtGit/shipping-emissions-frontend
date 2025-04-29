import {
  Actions,
  BlockURL,
  ContainsSelector,
  DomainRules,
  ElementHidingSelectors,
  HasSelector,
  HeuristicRule,
  HeuristicsRulesParams,
  NotSelector,
  ProcessedRules,
  PropertiesSelector,
  RuleType,
  Selector,
  SelectorObj,
  XPathSelector,
} from "@/content-scripts/heuristics-db/types";
import { SelectorParser } from "@/content-scripts/heuristics-db/selector-parser";

import {
  MSG_GET_HEURISTICS_DATABASE,
  MSG_GET_HEURISTICS_URLS_TO_BLOCK,
  ruleSeparatorRegexInstance,
} from "@/app/scripts/app-consts";

export const heuristicsElementsToRemove = new Set<Element>();
export const heuristicsUrlsToBlock = new Set<BlockURL>();

export const downloadHeuristicsDB = (): Promise<ProcessedRules | {}> =>
  new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      {
        type: MSG_GET_HEURISTICS_DATABASE,
      },
      resolve
    );
  });

export const sendHeuristicsURLsToBlock = (): Promise<ProcessedRules | string> =>
  new Promise((resolve, reject) => {
    if (heuristicsUrlsToBlock.size > 0) {
      chrome.runtime.sendMessage(
        {
          type: MSG_GET_HEURISTICS_URLS_TO_BLOCK,
          heuristicsUrlsToBlockArray: Array.from(heuristicsUrlsToBlock),
        },
        resolve
      );
    } else {
      resolve("Nothing to block");
    }
  });
export const processHeuristicsRules = async (
  processedRules: ProcessedRules | {},
  currentUrl: string
) => {
  const isEmpty = (o) => !o || Object.keys(o).length === 0;
  const currentDomain = new URL(currentUrl).hostname;
  const parser = new SelectorParser();

  Object.entries(processedRules).forEach(([type, rules]) => {
    if (isEmpty(rules)) return;

    switch (type as RuleType) {
      case RuleType.ADSERVER:
      case RuleType.PHISHING:
      case RuleType.SCAM:
        const isPageBlock = [RuleType.SCAM, RuleType.PHISHING].includes(
          type as RuleType
        );

        Object.entries(rules as DomainRules).forEach(
          ([selectorsType, selectorsByDomain]) => {
            if (
              ![
                ElementHidingSelectors["#?#"],
                ElementHidingSelectors["##"],
              ].includes(selectorsType as ElementHidingSelectors)
            ) {
              window.useLogging && console.warn(
                "processHeuristicsRules:Unexpected selectorsType:",
                selectorsType
              );
              return null;
            }

            processSelectorsByDomain(selectorsByDomain, currentUrl).forEach(
              (selectors) => {
                selectors.forEach(async ({ selector, isSilent, ...rest }) => {
                  try {
                    const parsedSelectors = parser.parseSelector(selector);
                    if (!parsedSelectors) return;

                    const elements = getElementsByRule(parsedSelectors);
                    if (elements.length === 0) return;

                    if (isPageBlock) {
                      heuristicsUrlsToBlock.add({
                        domain: currentDomain,
                        isSilent: isSilent || false,
                        type: type as RuleType,
                        source: selector,
                        id: rest.id
                      });
                    } else {
                      elements.forEach((element) =>
                        heuristicsElementsToRemove.add(element)
                      );
                    }
                  } catch (error) {
                    window.useLogging && console.error("processSelectorsByDomain", error);
                    throw error;
                  }
                });
              }
            );
          }
        );
        break;
      default:
        return;
    }
  });
};

type PatternInput = string | RegExp;

export const checkUrlAgainstCurrentDomain = (
  pattern: PatternInput,
  href: string | undefined
): boolean => {
  try {
    if (!href) return false;
    const urlRegex = new RegExp(pattern, "i");
    return urlRegex.test(href);
  } catch {
    if (typeof pattern === "string" && href) {
      return pattern === "" || pattern === "*" || href.includes(pattern);
    }
    return false;
  }
};

export function processSelectorsByDomain(
  selectorsByDomain: SelectorObj,
  href: string
) {
  let parsedSelectorsToReturn: SelectorObj[][] = [];
  Object.entries(selectorsByDomain).forEach(([domainRegex, selectors]) => {
    const applyForDomain = checkUrlAgainstCurrentDomain(domainRegex, href);
    if (Array.isArray(selectors) && selectors.length > 0 && applyForDomain) {
      parsedSelectorsToReturn.push(selectors);
    }
  });
  return parsedSelectorsToReturn;
}

/**
 * Processes heuristic rules for ads, scams, and phishing
 * @param heuristicsContent Array of heuristic rules to process
 * @returns Processed rules organized by type and domain
 */
export async function processHeuristics(
  heuristicsContent: HeuristicRule[]
): Promise<ProcessedRules> {
  const processedRules: ProcessedRules = {
    adserver: {},
    whitelist: {},
    scam: {},
    phishing: {},
    action: [],
    title: [],
    description: [],
    cleanName: "heuristics",
    version: "3.0.0",
    name: "mbgc.db.heuristics.json.2",
  };

  // Process each rule
  for (const rule of heuristicsContent) {
    if (!isValidHeuristicsRule(rule)) continue;
    const { r: ruleContent, s: isSilent, t: type, a: isAggressiveMode, id } = rule;
    if (!ruleContent || !type) continue;

    const params: HeuristicsRulesParams = {
      isSilent,
      isAggressiveMode: isAggressiveMode || false,
      id
    };

    switch (type) {
      case RuleType.ADSERVER:
        processRule(ruleContent, processedRules.adserver);
        break;
      case RuleType.SCAM:
        processRule(ruleContent, processedRules.scam, params);
        break;
      case RuleType.PHISHING:
        processRule(ruleContent, processedRules.phishing, params);
        break;
    }
  }
  return processedRules;
}

type RuleComponents = {
  domain: string;
  separator: string;
  selector: string;
};

const splitRule = (rule: string): RuleComponents | null => {
  // Regex pattern to match both ## and #?# separators

  const match = rule.match(ruleSeparatorRegexInstance);
  if (!match) {
    return null;
  }

  // Destructure after we know match is not null
  // match[0] is the full match, match[1-3] are the capture groups
  return {
    domain: match[1],
    separator: match[2],
    selector: match[3],
  };
};

/**
 * Process an individual ad rule and add it to the domain rules
 */
function processRule(
  ruleContent: string,
  rules: DomainRules,
  restParams?: HeuristicsRulesParams
): void {
  const res = splitRule(ruleContent);

  if (!res) {
    window.useLogging && console.debug("PR: Error splitRule: ", ruleContent);
    return;
  }

  let { domain, separator, selector } = res;
  if (domain == "") domain = "*";
  separator = ElementHidingSelectors[separator];

  rules[separator] = rules[separator] || {};

  // Process domain-specific rules

  rules[separator][domain] = rules[separator][domain] || [];

  if (selector) {
    rules[separator][domain].push({
      selector,
      ...(restParams !== undefined ? restParams : {}),
    });
  }
}

/**
 * Validates if a heuristic rule has the required properties
 */
const isValidHeuristicsRule = (rule: unknown): rule is HeuristicRule => {
  if (!rule || typeof rule !== "object") {
    return false;
  }

  const typedRule = rule as Record<string, unknown>;

  return (
    typeof typedRule.r === "string" &&
    (typeof typedRule.s === "boolean" || typedRule.s === null) &&
    typeof typedRule.t === "string" &&
    isValidRuleType(typedRule.t)
  );
};

// Type guard for rule type
const isValidRuleType = (type: unknown): type is RuleType =>
  typeof type === "string" && ["adserver", "scam", "phishing"].includes(type);

/**
 * Gets DOM elements matching a specific rule set
 * @param rules Array of selector rules to process
 * @returns Array of matching DOM elements
 */
export const getElementsByRule = (rules: Selector[] | null): Element[] => {
  let elements: Element[] = [];
  let isFirstRule = true;

  if (rules == null) return elements;
  for (const rule of rules) {
    if (isFirstRule) {
      elements = processInitialSimpleSelectors(rule);
      isFirstRule = false;
    } else {
      elements = filterElementsByRule(elements, rule);
    }
    // If no elements match at any point, we can stop processing
    if (elements.length === 0) {
      break;
    }
  }

  return elements;
};

/**
 * Perform the specified action on elements matching the selector
 * @param selector - The CSS selector to match elements
 * @param action - The action to perform on matched elements
 */
const performActionOnElements = (selector: string, action: Actions) => {
  Array.from(document.querySelectorAll(selector)).forEach((element) => {
    switch (action) {
      case Actions.CLICK_ON_ELEMENT:
        if (element instanceof HTMLElement) {
          element.click();
        }
        break;
      case Actions.REMOVE_ELEMENT:
        element.remove();
        break;
    }
  });
};
/**
 * Process initial simple selectors and return matching elements
 * @param rule - The selector rule to process
 * @returns Array of matching DOM elements
 */

const processInitialSimpleSelectors = (rule: Selector): Element[] => {
  switch (rule.type) {
    case "plain":
      if (typeof document !== "undefined") {
        if (rule.action) {
          performActionOnElements(rule.selector, rule.action);
          return [];
        }
        if (rule.selector.startsWith("/") && rule.selector.endsWith("/")) {
          const regex = new RegExp(rule.selector.slice(1, -1), "i");
          return Array.from(document.querySelectorAll("*")).filter((element) =>
            regex.test(element.textContent ?? "")
          );
        }
        let result = [];
        try {
          result = Array.from(document.querySelectorAll(rule.selector));
        } catch (error) {
          window.useLogging && console.error("Error in querySelectorAll", error);
        }
        return result;
      } else {
        window.useLogging && console.log("DEBUG:document undefined");
        return [];
      }
    case "contains":
      return [];
    case "xpath":
      return evaluateXPathSelector(rule);
    default:
      window.useLogging && console.warn(`Unexpected initial selector type: ${rule.type}`);
      return [];
  }
};

/**
 * Filter elements based on a selector rule
 */
const filterElementsByRule = (
  elements: Element[],
  rule: Selector
): Element[] => {
  switch (rule.type) {
    case "plain":
      return elements.filter((element) => element.matches(rule.selector));
    case "contains":
      return filterByContains(elements, rule);
    case "has":
      return filterByHas(elements, rule);
    case "not":
      return filterByNot(elements, rule);
    case "properties":
      return filterByProperties(elements, rule);
    case "xpath":
      return filterByXPath(elements, rule);
    default:
      window.useLogging && console.warn(`Unknown selector type: ${(rule as Selector).type}`);
      return elements;
  }
};

/**
 * Filter elements that contain specific text patterns
 * @param elements - Array of DOM elements to filter
 * @param rule - Contains selector rule with text patterns
 * @returns Array of elements that match the text patterns
 */
const filterByContains = (
  elements: Element[],
  rule: ContainsSelector
): Element[] => {
  // Create a single regex pattern that matches any of the text patterns
  const regexPattern = rule.text.startsWith("/") && rule.text.endsWith("/") ? 
    new RegExp(rule.text.slice(1, -1), "i") : new RegExp(`${rule.text}`, "i");
  return elements.filter((element) => {
    const elementText = element.textContent ?? "";
    let normalizedSearchText = elementText.toLowerCase().trim();
    return regexPattern.test(normalizedSearchText);
  });
};
/**
 * Filter elements that have child elements matching selectors
 */
const filterByHas = (elements: Element[], rule: HasSelector): Element[] => {
  return elements.filter((element) => {
    const childElements = getElementsByRule(rule.selectors);
    const hasMatchingChild = childElements.some((child) =>
      element.contains(child)
    );
    if (!hasMatchingChild) return false;
    return hasMatchingChild;
  });
};

/**
 * Filter elements that don't match the given selectors
 */
const filterByNot = (
  matchingElements: Element[],
  rule: NotSelector
): Element[] => {
  const excludedElements = getElementsByRule(rule.selectors);
  return matchingElements.filter(
    (element) => !excludedElements.includes(element)
  );
};


/**
 * Filter elements by computed style properties
 */
const filterByProperties = (
  elements: Element[],
  rule: PropertiesSelector
): Element[] => {

  const cleanedStyle = rule.propertyFilter.trim(); // only trim, dont remove spaces.
  if (cleanedStyle.length === 0) return [];

  const propsKeys = cleanedStyle.split(';').map((oneStyle) => oneStyle.split(':')[0].trim());

  const dummyElement = createDummyHTMLElement(cleanedStyle);
  document.body.appendChild(dummyElement);

  elements = elements.filter((element) => {
    
    if (!(element instanceof HTMLElement)) return false;

    return hasAllStyles(element, dummyElement, propsKeys);
  });

  document.body.removeChild(dummyElement);

  return elements;
};

// Function to create a dummy element with the given styles
function createDummyHTMLElement(styleString: string): HTMLElement {

  const dummyElement = document.createElement('section');
  const forceHide = 'display: none !important;';
  
  // make sure the dummy element is not visible
  dummyElement.style.cssText = styleString + forceHide;
      
  return dummyElement;
}

// Function to compare computed styles of two elements
function hasAllStyles(realElement:HTMLElement, dummyElement:HTMLElement, properties: string[]): Boolean {
      // Get computed styles for both elements
    const realComputedStyle = window.getComputedStyle(realElement);
    const dummyComputedStyle = window.getComputedStyle(dummyElement);

    // Iterate through all styles in the dummy element
    for (const property of properties) {

        const dummyValue = dummyComputedStyle.getPropertyValue(property).trim();
        const realValue = realComputedStyle.getPropertyValue(property).trim();

        // If the property in dummy doesn't match real, return false
        if (dummyValue && dummyValue !== realValue) {
            // Mismatch found for property
            return false;
        }
    }

    // If all styles match, return true
    return true;
}

/**
 * Evaluate XPath selector and return matching elements
 */
const evaluateXPathSelector = (rule: XPathSelector): Element[] => {
  try {
    const result = document.evaluate(
      rule.xpath,
      document,
      null,
      XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
      null
    );

    const elements: Element[] = [];
    for (let i = 0; i < result.snapshotLength; i++) {
      const element = result.snapshotItem(i) as Element;
      if (element) elements.push(element);
    }
    return elements;
  } catch (error) {
    window.useLogging && console.error("XPath evaluation error:", error);
    return [];
  }
};

/**
 * Filter elements by XPath expression
 */
const filterByXPath = (elements: Element[], rule: XPathSelector): Element[] => {
  const xpathElements = evaluateXPathSelector(rule);
  return elements.filter((element) => xpathElements.includes(element));
};
