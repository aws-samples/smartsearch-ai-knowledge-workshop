import React, { useState } from "react";

import { Button, Input, Grid, FormField } from "@cloudscape-design/components";
import { MAIN_API, HEADERS } from "../../tools/constants";

import axios from "axios";

const ANSWER_API = MAIN_API + "/smart_search";

const MainSearchTable = ({
  setQuery,
  setNewItems,
  btnLoading,
  setBtnLoading,
}) => {
  const [filteringText, setFilteringText] = useState("");

  const search = () => {
    if (!filteringText) {
      alert("Please input your question");
      return;
    }

    setBtnLoading(true);
    setNewItems([]);

    setQuery(filteringText);

    axios({
      method: "POST",
      url: ANSWER_API,
      headers: HEADERS,
      data: JSON.stringify({
        search_words: filteringText,
        manufacturing_process_number: "",
      }),
    })
      .then((response) => {
        const _tmp_data = [];
        if (!response || !response.data || !Array.isArray(response.data)) {
          setNewItems(_tmp_data);
        }

        response.data.forEach((item) => {
          if (!item["source"]) {
            return;
          }
          let _tmp = {};
          const sourceKey = Object.keys(item["source"]);
          sourceKey.forEach((itemKey) => {
            _tmp[itemKey] = item["source"][itemKey];
          });
          _tmp["id"] = item["id"];
          const uploadDateList = item["source"]["upload_date"]
            ? item["source"]["upload_date"].split(",")
            : null;
          _tmp["upload_date"] = uploadDateList
            ? uploadDateList[uploadDateList.length - 1]
            : "";
          _tmp_data.push(_tmp);
        });

        setNewItems(_tmp_data);
        setQuery(filteringText);
        return;
      })
      .finally(() => {
        setBtnLoading(false);
      });
  };

  return (
    <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
      <FormField
        label={
          <div>
            Search question<span className="must-input">*</span>
          </div>
        }
      >
        <Input
          onChange={({ detail }) =>
            setFilteringText(detail.value?.substring(0, 200))
          }
          value={filteringText}
          placeholder="[Required] Please enter search content"
        />
      </FormField>
      <FormField label="Operate">
        <Button onClick={() => search()} loading={btnLoading} iconName="search">
          Search
        </Button>
      </FormField>
    </Grid>
  );
};

export default MainSearchTable;
