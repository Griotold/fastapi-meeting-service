def deduplicate_and_sort(items: list[str]) -> list[str]:
    """
    List 값의 중복을 제거하고 원래 순서대로 정렬
    
    >>> deduplicate_and_sort(['apple', 'banana', 'apple', 'cherry'])
    ['apple', 'banana', 'cherry']
    
    >>> deduplicate_and_sort(['c', 'a', 'b', 'a', 'c'])
    ['c', 'a', 'b']
    
    >>> deduplicate_and_sort([])
    []
    
    >>> deduplicate_and_sort(['single'])
    ['single']
    
    >>> deduplicate_and_sort(['a', 'a', 'a'])
    ['a']
    """
    # dict.fromkeys() 는 순서가 보장된다.
    return list(dict.fromkeys(items))