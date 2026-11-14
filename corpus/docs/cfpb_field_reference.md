# CFPB Consumer Complaint Database: Field reference

Source: https://cfpb.github.io/api/ccdb/fields.html (CFPB Open Tech). As a work of the United States Government,
source code released by the CFPB is in the public domain by default within the United States.

The following fields are currently included in the Consumer Complaint Database.

## Date received

The date the CFPB received the complaint. Data type: date and time.

## Product

The type of product the consumer identified in the complaint. Data type: plain text. This field is a categorical variable.

## Sub-product

The type of sub-product the consumer identified in the complaint. Data type: plain text. This field is a categorical variable. Not all Products have Sub-products.

## Issue

The issue the consumer identified in the complaint. Data type: plain text. This field is a categorical variable. Possible values are dependent on Product.

## Sub-issue

The sub-issue the consumer identified in the complaint. Data type: plain text. This field is a categorical variable. Possible values are dependent on product and issue. Not all Issues have corresponding Sub-issues.

## Company public response

The company's optional, public-facing response to a consumer's complaint. Companies can choose to select a response from a pre-set list of options that will be posted on the public database. For example, "Company believes complaint is the result of an isolated error." Data type: plain text.

Companies' public-facing responses to complaints are included if companies choose to publish one. Companies may select a public response from a set list of options as soon as they respond to the complaint, but no later than 180 days after the complaint was sent to the company for response.

## Company

The complaint is about this company. Data type: plain text. This field is a categorical variable.

## State

The state of the mailing address provided by the consumer. Data type: plain text. This field is a categorical variable.

## ZIP code

The mailing ZIP code provided by the consumer. Data type: plain text.

The 5-digit United States Postal Service ZIP code will be published where provided unless the consumer lived in a ZIP code aligned to a United States Census Bureau ZIP Code Tabulation Area (ZCTA) with fewer than 20,000 people. In those cases, where the Census ZCTA had fewer than 20,000 people, the 3-digit ZIP code will be published if the 3-digit ZCTA has more than 20,000 people. Otherwise, no ZIP code will be published.

## Tags

Data that supports easier searching and sorting of complaints submitted by or on behalf of consumers. Data type: plain text.

For example, complaints where the submitter reports the age of the consumer as 62 years or older are tagged, 'Older American.' Complaints submitted by or on behalf of a servicemember or the spouse or dependent of a servicemember are tagged, 'Servicemember.' Servicemember includes anyone who is active duty, National Guard, or Reservist, as well as anyone who previously served and is a Veteran or retiree.

## Submitted via

How the complaint was submitted to the CFPB. Data type: plain text. This field is a categorical variable.

## Date sent to company

The date the CFPB sent the complaint to the company. Data type: date and time.

## Company response to consumer

This is how the company responded. For example, "Closed with explanation." Data type: plain text. This field is a categorical variable.

## Timely response?

Whether the company gave a timely response. Data type: plain text, yes or no.

## Complaint ID

The unique identification number for a complaint. Data type: number.
