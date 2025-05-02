import { S3Client, ListBucketsCommand } from "@aws-sdk/client-s3";

// a client can be shared by different commands.
const client = new S3Client({ region: "us-east-2" });

const params = {
    /** input parameters */
};
const command = new ListBucketsCommand(params);