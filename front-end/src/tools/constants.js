// Below items needs to be changed
// mainapi / opensearch_api / opensearch_region / SOURCE_DATA_BUCKET
export const MAIN_API = process.env.REACT_APP_MAIN_API;
export const opensearch_api = process.env.REACT_APP_OPENSEARCH_API;
export const opensearch_region = process.env.REACT_APP_OPENSEARCH_REGION;
export const SOURCE_DATA_BUCKET =
  process.env.REACT_APP_SOURCE_DATA_BUCKET || "";

export const HEADERS = { "Content-Type": "application/json" };
export const POST_HEADERS = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*",
};
export const SOURCE_DATA_BUCKET_PREFIX = "source_data/";
export var last_table_name = "FeedbackRecordsSEWCFAQ";

export const FILE_TYPES = [
  { value: "faq", label: "FAQ Document" },
  { value: "content_search", label: "Content Search Document" },
];
export const mainapi_env = process.env.REACT_APP_MAIN_API;
export const SUMMARIZE_API = process.env.REACT_APP_SUMMARIZE_API
  ? process.env.REACT_APP_SUMMARIZE_API
  : MAIN_API + "/summarize";
