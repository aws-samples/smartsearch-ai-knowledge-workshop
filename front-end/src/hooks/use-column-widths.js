// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { useMemo } from "react";
import {
  addToColumnDefinitions,
  mapWithColumnDefinitionIds,
} from "../tools/columnDefinitionsHelper";
import { useLocalStorage } from "./localStorage";

export function useColumnWidths(storageKey, columnDefinitions) {
  const [widths, saveWidths] = useLocalStorage(storageKey);

  function handleWidthChange(event) {
    saveWidths(
      mapWithColumnDefinitionIds(
        columnDefinitions,
        "width",
        event.detail.widths
      )
    );
  }
  const memoDefinitions = useMemo(() => {
    return addToColumnDefinitions(columnDefinitions, "width", widths);
  }, [widths, columnDefinitions]);

  return [memoDefinitions, handleWidthChange];
}
