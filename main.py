import asyncio
import os
import argparse
from pathlib import Path
from src.graph import video_memory_graph    


import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_benchmark_files(benchmark_dir, category='all'):
    """
    Get benchmark case files based on category
    Args:
        benchmark_dir: root benchmark directory
        category: 'all', 'character', 'prop', or 'scene'
    Returns:
        List of tuples (full_path, relative_path, category_type)
    """
    benchmark_path = Path(benchmark_dir)
    files = []
    
    categories = ['character', 'prop', 'scene'] if category == 'all' else [category]
    priority_map = {'character': 3, 'prop': 2, 'scene': 1}
    
    for cat in categories:
        cat_path = benchmark_path / cat
        if cat_path.exists():
            # Get all .txt files in this category
            for txt_file in cat_path.rglob('*.txt'):
                rel_path = txt_file.relative_to(benchmark_path)
                files.append((str(txt_file), str(rel_path), cat, priority_map[cat]))
    
    # Sort by priority (character > prop > scene)
    files.sort(key=lambda x: x[3], reverse=True)
    
    return files

async def main(category='all'):
    """
    Main function to process benchmark cases
    Args:
        category: 'all', 'character', 'prop', or 'scene'
    """
    benchmark_dir = "datasets/benchmark"
    
    # Get files based on category
    case_files = get_benchmark_files(benchmark_dir, category)
    
    logger.info(f"Processing category: {category}")
    logger.info(f"Found {len(case_files)} benchmark cases")
    
    for index, (file_path, relative_path, cat, _) in enumerate(case_files, 1):
        # Extract case name and create numbered case name
        case_name = Path(relative_path).stem  # Remove .txt extension
        numbered_case_name = f"case{index}_{case_name}"
        
        # Create thread_id: benchmark/{category}/shot_X/case{index}_{name}
        output_path = Path(relative_path).parent / numbered_case_name
        thread_id = f"benchmark/{output_path}"
        
        logger.info(f"[{index}/{len(case_files)}] Processing: {numbered_case_name} ({cat})")
        logger.info(f"Output: output/{thread_id}")
        
        try:
            # Read script file
            with open(file_path, "r") as f:
                raw_script = f.read()

            # Configure and run the graph
            config = {"configurable": {"thread_id": thread_id}}
            input_data = {"messages": [("user", raw_script)]}

            async for msgs in video_memory_graph.astream(
                input=input_data, 
                stream_mode="values", 
                config=config
            ):
                msgs['messages'][-1].pretty_print()
                
            logger.info(f"✓ Successfully processed: {numbered_case_name}")
            
        except Exception as e:
            logger.error(f"✗ Error processing {numbered_case_name}: {e}")
            continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Process benchmark video memory cases'
    )
    parser.add_argument(
        '--category',
        type=str,
        choices=['all', 'character', 'prop', 'scene'],
        default='all',
        help='Category to process (default: all)'
    )
    
    args = parser.parse_args()
    asyncio.run(main(category=args.category))