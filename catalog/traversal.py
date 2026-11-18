def collect(source, library, region):
    pages = 0
    seen = set()
    for page in source.pages(region):
        for record in page['items']:
            library.apply(region, record)
            seen.add(record['id'])
        pages += 1
    return {'region': region, 'pages': pages, 'observed': sorted(seen)}
