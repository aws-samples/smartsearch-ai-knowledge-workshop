import { TableHeader } from "../common/common-components";

const FullPageHeader = ({ resourceName = "知识库查询结果", ...props }) => {
  return <TableHeader title={resourceName} {...props} />;
};
export default FullPageHeader;
