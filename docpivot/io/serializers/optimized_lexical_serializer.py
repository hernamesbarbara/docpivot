# This file has been removed.
# The OptimizedLexicalDocSerializer functionality has been merged into the base LexicalDocSerializer class.
# Use LexicalDocSerializer with performance configuration options instead:
#
# from docpivot.io.serializers.lexicaldocserializer import LexicalDocSerializer, LexicalParams
#
# params = LexicalParams(
#     enable_streaming=True,
#     use_fast_json=True,
#     parallel_processing=True,
#     batch_size=1000,
#     memory_efficient_mode=True,
#     progress_callback=callback_func
# )
#
# serializer = LexicalDocSerializer(doc=doc, params=params)
