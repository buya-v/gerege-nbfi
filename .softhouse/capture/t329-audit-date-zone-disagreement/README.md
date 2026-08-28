# T329 — audit: oracle reports two different dates for the same instant (WIP stub)

WIP: two paths located.
- /journalentries -> Gson DefaultToApiJsonSerializer -> core/api/LocalDateAdapter -> ARRAY
- /glclosures -> returns POJO from JAX-RS -> Jackson -> ISO STRING
