SELECT encode(sha256(convert_to(coalesce(string_agg(tag || ':' || id || ':' || version, ',' ORDER BY tag, id), ''), 'UTF8')), 'hex'), count(*) FROM (
SELECT 'user' AS tag, q.* FROM (SELECT id::text, xmin::text || ':' || ctid::text FROM core_user WHERE id = %(subject)s) AS q(id, version)
UNION ALL
SELECT 'person' AS tag, q.* FROM (SELECT id::text, xmin::text || ':' || ctid::text FROM core_person WHERE id = %(person)s) AS q(id, version)
UNION ALL
SELECT 'person_phone' AS tag, q.* FROM (SELECT c.id::text, c.xmin::text || ':' || c.ctid::text FROM core_phoneclaim c JOIN core_person p ON p.phone_claim_id = c.id WHERE p.id = %(person)s) AS q(id, version)
UNION ALL
SELECT 'listing' AS tag, q.* FROM (SELECT id::text, xmin::text || ':' || ctid::text FROM listings_listing WHERE id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'revision' AS tag, q.* FROM (SELECT id::text, xmin::text || ':' || ctid::text FROM listings_revision WHERE listing_id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'revision_category' AS tag, q.* FROM (SELECT rc.id::text, rc.xmin::text || ':' || rc.ctid::text FROM listings_revision_categories rc JOIN listings_revision r ON r.id = rc.revision_id WHERE r.listing_id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'category' AS tag, q.* FROM (SELECT DISTINCT c.id::text, c.xmin::text || ':' || c.ctid::text FROM catalog_category c JOIN listings_revision_categories rc ON rc.category_id = c.id JOIN listings_revision r ON r.id = rc.revision_id WHERE r.listing_id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'revision_service' AS tag, q.* FROM (SELECT rs.id::text, rs.xmin::text || ':' || rs.ctid::text FROM listings_revision_services rs JOIN listings_revision r ON r.id = rs.revision_id WHERE r.listing_id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'service' AS tag, q.* FROM (SELECT DISTINCT s.id::text, s.xmin::text || ':' || s.ctid::text FROM catalog_service s JOIN listings_revision_services rs ON rs.service_id = s.id JOIN listings_revision r ON r.id = rs.revision_id WHERE r.listing_id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'revision_travel' AS tag, q.* FROM (SELECT rt.id::text, rt.xmin::text || ':' || rt.ctid::text FROM listings_revision_travel_areas rt JOIN listings_revision r ON r.id = rt.revision_id WHERE r.listing_id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'municipality' AS tag, q.* FROM (SELECT DISTINCT m.id::text, m.xmin::text || ':' || m.ctid::text FROM catalog_municipality m JOIN listings_revision r ON r.listing_id = %(listing)s AND (r.municipality_id = m.id OR EXISTS (SELECT 1 FROM listings_revision_travel_areas rt WHERE rt.revision_id = r.id AND rt.municipality_id = m.id))) AS q(id, version)
UNION ALL
SELECT 'postal_code' AS tag, q.* FROM (SELECT DISTINCT pc.id::text, pc.xmin::text || ':' || pc.ctid::text FROM catalog_postalcode pc JOIN listings_revision r ON r.postal_code_id = pc.id WHERE r.listing_id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'zone' AS tag, q.* FROM (SELECT DISTINCT z.id::text, z.xmin::text || ':' || z.ctid::text FROM catalog_zone z JOIN listings_revision r ON r.zone_id = z.id WHERE r.listing_id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'rate' AS tag, q.* FROM (SELECT t.id::text, t.xmin::text || ':' || t.ctid::text FROM listings_rate t JOIN listings_revision r ON r.id = t.revision_id WHERE r.listing_id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'photo' AS tag, q.* FROM (SELECT ph.id::text, ph.xmin::text || ':' || ph.ctid::text FROM mediafiles_photo ph JOIN listings_revision r ON r.id = ph.revision_id WHERE r.listing_id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'blob' AS tag, q.* FROM (SELECT DISTINCT b.id::text, b.xmin::text || ':' || b.ctid::text FROM mediafiles_blob b JOIN mediafiles_photo ph ON ph.blob_id = b.id JOIN listings_revision r ON r.id = ph.revision_id WHERE r.listing_id = %(listing)s) AS q(id, version)
UNION ALL
SELECT 'verification' AS tag, q.* FROM (SELECT id::text, xmin::text || ':' || ctid::text FROM core_verificationcheck WHERE person_id = %(person)s AND subject_id = %(subject)s) AS q(id, version)
UNION ALL
SELECT 'representation' AS tag, q.* FROM (SELECT id::text, xmin::text || ':' || ctid::text FROM core_representationaction WHERE person_id = %(person)s AND subject_id = %(subject)s) AS q(id, version)
UNION ALL
SELECT 'representation_document' AS tag, q.* FROM (SELECT DISTINCT d.id::text, d.xmin::text || ':' || d.ctid::text FROM core_legaldocument d JOIN core_representationaction a ON a.document_id = d.id WHERE a.person_id = %(person)s AND a.subject_id = %(subject)s) AS q(id, version)
UNION ALL
SELECT 'acceptance' AS tag, q.* FROM (SELECT id::text, xmin::text || ':' || ctid::text FROM core_legalacceptance WHERE user_id = %(subject)s) AS q(id, version)
UNION ALL
SELECT 'acceptance_document' AS tag, q.* FROM (SELECT DISTINCT d.id::text, d.xmin::text || ':' || d.ctid::text FROM core_legaldocument d JOIN core_legalacceptance a ON a.document_id = d.id WHERE a.user_id = %(subject)s) AS q(id, version)
UNION ALL
SELECT 'personal_phone' AS tag, q.* FROM (SELECT id::text, xmin::text || ':' || ctid::text FROM core_phoneclaim WHERE individual_id = %(subject)s AND agency_id IS NULL) AS q(id, version)
UNION ALL
SELECT 'owned_agency' AS tag, q.* FROM (SELECT id::text, xmin::text || ':' || ctid::text FROM core_agency WHERE owner_id = %(subject)s) AS q(id, version)
UNION ALL
SELECT 'membership' AS tag, q.* FROM (SELECT id::text, xmin::text || ':' || ctid::text FROM core_agencymember WHERE user_id = %(subject)s) AS q(id, version)
UNION ALL
SELECT 'favorite' AS tag, q.* FROM (SELECT id::text, xmin::text || ':' || ctid::text FROM listings_favorite WHERE user_id = %(subject)s) AS q(id, version)
) AS rows;
