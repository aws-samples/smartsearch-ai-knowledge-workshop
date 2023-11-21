// Below items needs to be changed
// mainapi / opensearch_api
export const MAIN_API = process.env.REACT_APP_MAIN_API;

export const HEADERS = { "Content-Type": "application/json" };

export const SUMMARIZE_API = process.env.REACT_APP_SUMMARIZE_API
  ? process.env.REACT_APP_SUMMARIZE_API
  : MAIN_API + "/summarize";
