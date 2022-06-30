# -*- coding: utf-8 -*-

import json

BASE_URL = 'https://shiza-project.com'
BASE_API_URL = BASE_URL + '/graphql'


def mpaa_rus(mpaa):
    return {'G':'0+', 'PG':'6+', 'PG_13':'12+', 'R':'16+'}.get(mpaa, '18+')

def get_genres(genres):
    return ', '.join([g['name'] for g in genres])

def get_season(node):
    return u'{0}{1}'.format({'WINTER':u'зима ', 'FALL':u'осень ', 'SUMMER':u'лето ', 'SPRING':u'весна '}.get(node['season'], ''), node['seasonYear'])

def get_poster(node):
    return node['posters'][0]['preview']['url'] if node['posters'] else '{}/_nuxt/img/no-poster.313f19e.png'.format(BASE_URL)


ITEMS_PER_PAGE = 18

FETCH_RELEASES = {"operationName":"fetchReleases",
           "variables": {"first": ITEMS_PER_PAGE, "airedOn": None, "query": "", 
                         "orderBy":     {"field": "PUBLISHED_AT","direction":"DESC"},
                         "type":        {"include":[],"exclude":[]},
                         "status":      {"include":[],"exclude":["DRAFT"]},
                         "activity":    {"include":[],"exclude":["WISH"]},
                         "rating":      {"include":[],"exclude":[]},
                         "season":      {"include":[],"exclude":[]},
                         "watchlist":   {"include":[],"exclude":[]},
                         "genre":       {"include":[],"exclude":[]},
                         "category":    {"include":[],"exclude":[]},
                         "tag":         {"include":[],"exclude":[]},
                         "studio":      {"include":[],"exclude":[]},
                         "staff":       {"include":[],"exclude":[]},
                         "contributor": {"include":[],"exclude":[]},
                        },
           "query":"""
query fetchReleases($first: Int, $after: String, $orderBy: ReleaseOrder, $query: String, $tag: ReleaseIDFilter, $category: ReleaseIDFilter, $genre: ReleaseIDFilter, $studio: ReleaseIDFilter, $type: ReleaseTypeFilter, $status: ReleaseStatusFilter, $rating: ReleaseRatingFilter, $airedOn: ReleaseAiredOnRangeFilter, $activity: ReleaseActivityFilter, $season: ReleaseSeasonFilter, $staff: ReleaseIDFilter, $contributor: ReleaseIDFilter, $watchlist: ReleaseWatchlistFilter, $watchlistUserId: ID) {
    releases(
        first: $first
        after: $after
        orderBy: $orderBy
        query: $query
        tag: $tag
        category: $category
        genre: $genre
        studio: $studio
        type: $type
        status: $status
        airedOn: $airedOn
        rating: $rating
        activity: $activity
        season: $season
        staff: $staff
        contributor: $contributor
        watchlist: $watchlist
        watchlistUserId: $watchlistUserId
    ) {
        totalCount
        edges {
            node {
                ...ReleaseCard
                viewerWatchlist {
                    id
                    status
                    __typename
                }
                reactionGroups {
                    count
                    content
                    viewerHasReacted
                    __typename
                }
                viewerInBlockedCountry
                __typename
            }
            __typename
        }
        pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
            __typename
        }
        __typename
    }
}

fragment ReleasePosterCommon on ImageFile {
    id
    preview: resize(width: 360, height: 500) {
        width
        height
        url
        __typename
    }
    original {
        width
        height
        url
        __typename
    }
    __typename
}

fragment ReleaseCard on Release {
    id
    slug
    name
    originalName
    airedOn
    releasedOn
    publishedAt
    announcement
    episodesCount
    episodesAired
    episodeDuration
    season
    seasonYear
    seasonNumber
    status
    activity
    type
    rating
    viewCount
    score
    posters {
        ...ReleasePosterCommon
        __typename
    }
    genres {
        id
        slug
        name
        __typename
    }
    viewerWatchlist {
        id
        status
        score
        episodes
        rewatches
        __typename
    }
    reactionGroups {
        count
        content
        viewerHasReacted
        __typename
    }
    __typename
}"""}


def _get_release_query(after=None, query=None):
    graphql = FETCH_RELEASES
    if after:
        graphql['variables'].update({'after':after})

    if query:
        graphql['variables'].update({'query':query})

    return graphql


def get_all_query(after=None, query=None):
    graphql = _get_release_query(after, query)
    graphql['variables']['activity'].update({'include': ['WORK_IN_PROGRESS', 'COMPLETED']})
    return json.dumps(graphql)


def get_ongoing_query(after=None):
    graphql = _get_release_query(after)
    graphql['variables']['status'].update({'include': ['ONGOING']})
    return json.dumps(graphql)


def get_workin_query(after=None):
    graphql = _get_release_query(after)
    graphql['variables']['activity'].update({'include': ['WORK_IN_PROGRESS']})
    return json.dumps(graphql)


def get_completed_query(after=None):
    graphql = _get_release_query(after)
    graphql['variables']['activity'].update({'include': ['COMPLETED']})
    return json.dumps(graphql)



FETCH_RELEASE = {"operationName": "fetchRelease",
            "variables": {"slug": ""},
            "query": """
query fetchRelease($slug: String!) {
    release(slug: $slug) {
        id
        slug
        malId
        name
        originalName
        alternativeNames
        description
        descriptionSource
        descriptionExternal
        descriptionAuthors {
            id
            slug
            username
            avatar {
                ...UserAvatarCommon
                __typename
            }
            __typename
        }
        cause
        announcement
        season
        seasonYear
        seasonNumber
        episodesCount
        episodesAired
        episodeDuration
        type
        status
        activity
        viewCount
        score
        rating
        origins
        countries
        airedOn
        releasedOn
        nextEpisodeAt
        cover {
            ...ReleaseCoverCommon
            __typename
        }
        posters {
            ...ReleasePosterCommon
            __typename
        }
        screenshots {
            ...ReleaseScreenshotCommon
            __typename
        }
        studios {
            id
            slug
            name
            __typename
        }
        categories {
            id
            slug
            name
            __typename
        }
        genres {
            id
            slug
            name
            __typename
        }
        tags {
            id
            slug
            name
            __typename
        }
        staff {
            ...ReleaseStaffCommon
            __typename
        }
        relations {
            ...ReleaseRelationCommon
            __typename
        }
        recommendations {
            ...ReleaseCard
            __typename
        }
        torrents {
            id
            synopsis
            downloaded
            seeders
            leechers
            size
            metadata
            videoFormat
            videoQualities
            magnetUri
            updatedAt
            file {
                id
                filesize
                url
                __typename
            }
            __typename
        }
        contributors {
            ...ReleaseContributorCommon
            __typename
        }
        arches {
            name
            range
            __typename
        }
        videos {
            ...ReleaseVideoCommon
            __typename
        }
        episodes {
            ...ReleaseEpisodeCommon
            __typename
        }
        links {
            type
            url
            __typename
        }
        viewerWatchlist {
            id
            status
            score
            episodes
            rewatches
            __typename
        }
        viewerFavorite {
            id
            __typename
        }
        reactionGroups {
            count
            content
            viewerHasReacted
            __typename
        }
        userWatchlistStatusDistributions {
            count
            status
            __typename
        }
        userWatchlistScoreDistributions {
            count
            score
            __typename
        }
        viewerInBlockedCountry
        __typename
    }
}

fragment ReleaseContributorCommon on ReleaseContributor {
    id
    startOn
    endOn
    tasks {
        type
        ranges
        __typename
    }
    user {
        id
        slug
        username
        verified
        avatar {
            ...UserAvatarCommon
            __typename
        }
        roles {
            id
            name
            displayColor
            __typename
        }
        __typename
    }
    community {
        id
        slug
        name
        verified
        avatar {
            id
            preview: resize(width: 192, height: 192) {
                width
                height
                url
                __typename
            }
        __typename
        }
        __typename
    }
    __typename
}

fragment ReleaseVideoCommon on VideoFile {
    id
    embedSource
    embedUrl
    __typename
}
    
fragment ReleaseEpisodeCommon on ReleaseEpisode {
    id
    name
    number
    duration
    type
    subtitle {
        id
        filename
        url
        __typename
    }
    videos {
        ...ReleaseVideoCommon
        __typename
    }
    __typename
}

fragment ReleasePosterCommon on ImageFile {
    id
    preview: resize(width: 360, height: 500) {
        width
        height
        url
        __typename
    }
    original {
        width
        height
        url
        __typename
    }
    __typename
}

fragment ReleaseCoverCommon on ImageFile {
    id
    original {
        height
        width
        url
        __typename
    }
    __typename
}

fragment ReleaseScreenshotCommon on ImageFile {
    id
    original {
        height
        width
        url
        __typename
    }
    preview: resize(width: 200, height: 150) {
        height
        width
        url
        __typename
    }
    __typename
}

fragment ReleaseRelationCommon on ReleaseRelation {
    id
    type
    destination {
        ...ReleaseCard
        __typename
    }
    __typename
}

fragment ReleaseStaffCommon on ReleaseStaff {
    id
    roles
    person {
        id
        slug
        name
        originalName
        __typename
    }
    __typename
}

fragment ReleaseCard on Release {
    id
    slug
    name
    originalName
    airedOn
    releasedOn
    publishedAt
    announcement
    episodesCount
    episodesAired
    episodeDuration
    season
    seasonYear
    seasonNumber
    status
    activity
    type
    rating
    viewCount
    score
    posters {
        ...ReleasePosterCommon
        __typename
    }
    genres {
        id
        slug
        name
        __typename
    }
    viewerWatchlist {
        id
        status
        score
        episodes
        rewatches
        __typename
    }
    reactionGroups {
        count
        content
        viewerHasReacted
        __typename
    }
    __typename
}

fragment UserAvatarCommon on ImageFile {
    id
    preview: resize(width: 192, height: 192) {
        width
        height
        url
        __typename
    }
    __typename
}
"""}


def get_release_query(slug):
    query = FETCH_RELEASE
    query['variables'].update({'slug': slug})
    return json.dumps(query)


FETCH_COLLECTIONS = {"operationName": "fetchCollections",
            "variables": {"first":ITEMS_PER_PAGE, "query": ""},
            "query":"""
query fetchCollections($first: Int, $after: String, $query: String, $orderBy: CollectionOrder) {
    collections(first: $first, after: $after, query: $query, orderBy: $orderBy) {
        totalCount
        edges {
            node {
                ...CollectionCommon
                previewItems {
                    ...CollectionItemCommon
                    __typename
                }
                __typename
            }
            __typename
        }
        pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
            __typename
        }
        __typename
    }
}

fragment CollectionItemCommon on CollectionItem {
    id
    group
    description
    collectionable {
        id
        ... on Release {
            ...ReleaseCard
            __typename
        }
        __typename
    }
    __typename
}

fragment CollectionCommon on Collection {
    id
    slug
    name
    content
    viewCount
    publishedAt
    author {
        id
        slug
        username
        discriminator
        avatar {
            ...UserAvatarCommon
            __typename
        }
        __typename
    }
    __typename
}

fragment ReleasePosterCommon on ImageFile {
    id
    preview: resize(width: 360, height: 500) {
        width
        height
        url
        __typename
    }
    original {
        width
        height
        url
        __typename
    }
    __typename
}

fragment ReleaseCard on Release {
    id
    slug
    name
    originalName
    airedOn
    releasedOn
    publishedAt
    announcement
    episodesCount
    episodesAired
    episodeDuration
    season
    seasonYear
    seasonNumber
    status
    activity
    type
    rating
    viewCount
    score
    posters {
        ...ReleasePosterCommon
        __typename
    }
    genres {
        id
        slug
        name
        __typename
    }
    viewerWatchlist {
        id
        status
        score
        episodes
        rewatches
        __typename
    }
    reactionGroups {
        count
        content
        viewerHasReacted
        __typename
    }
    __typename
}

fragment UserAvatarCommon on ImageFile {
    id
    preview: resize(width: 192, height: 192) {
        width
        height
        url
        __typename
    }
    __typename
}
"""}


def get_collections_query():
    query = FETCH_COLLECTIONS
    return json.dumps(query)
